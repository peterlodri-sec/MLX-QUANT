// Copyright © 2026 8b-is

#include <metal_simdgroup>
#include <metal_stdlib>

using namespace metal;

#define MLX_MTL_CONST static constant constexpr const

MLX_MTL_CONST int SIMD_SIZE = 32;

// BitNet b1.58 ternary quantization: 2-bit codes {0, 1, 2} decode to signed
// {-1, 0, 1} via code - 1. One real-valued scale per group (no bias). The
// packed buffer is 16 codes per uint32 word, LSB-first, on the host/CPU side
// (see mlx/backend/cpu/quantized.cpp) -- reinterpreted here as a uint8_t*
// (4 codes per byte), which is bit-for-bit identical on this little-endian
// target. `bits` is always 2 here; it stays a template parameter only to
// match the shared get_quantized_kernel_wrapped/get_template_definition
// dispatch machinery that every quantization mode goes through.
//
// Besides the standalone quantize/dequantize kernels, this file has exactly
// one fused matmul kernel: ternary_qmv_fast, covering the single most common
// shape (non-batched weights, transpose == true, K%512==0, N%8==0 -- the
// nn.Linear/decode case). It does not cover qmv/qmv_wide/qmm/qmm_splitk/qvm/
// qvm_split_k -- mlx::quantized_matmul gates ternary_qmv_fast's use on
// exactly its precondition (see mlx/ops.cpp) and composes dequantize +
// the existing dense matmul for everything else, so no shape/dtype
// combination can reach a kernel name that was never written.
//
// Numerical note: unlike affine_quantize's scale (a min/max range, which is
// order-independent -- min and max never disagree regardless of reduction
// order), this kernel's scale is mean(|w|), a sum, and floating-point
// addition is not associative. simd_sum below is a parallel (tree) lane
// reduction, so it can legitimately disagree with a sequentially-computed
// reference sum in the last bit or two. That almost never changes the
// quantized result -- except for a weight whose w/scale ratio lands almost
// exactly on a round()-tie (near +/-0.5), where the tiniest scale
// difference flips which side it rounds to. This is real, bounded (at most
// one code step, ~2% of random draws in testing), and inherent to any
// summation-based scale compared against a differently-ordered reference;
// it is not fixable by "aligning" simd_sum's reduction order with some
// particular CPU implementation's order, since that would just match one
// arbitrary reference rather than remove the non-associativity itself. See
// assert_ternary_gpu_allclose in python/tests/test_quantized.py.

template <typename T, const int group_size, const int bits>
[[kernel]] void ternary_quantize(
    const device T* w [[buffer(0)]],
    device uint8_t* out [[buffer(1)]],
    device T* scales [[buffer(2)]],
    uint2 index [[thread_position_in_grid]],
    uint2 grid_dim [[threads_per_grid]]) {
  static_assert(bits == 2, "ternary quantization requires bits == 2");
  static_assert(
      group_size % SIMD_SIZE == 0,
      "Group size must be divisible by the SIMD width.");

  constexpr float eps = 1e-7;
  constexpr int pack_factor = 8 / bits; // codes per byte
  constexpr int values_per_reduce = group_size / SIMD_SIZE;
  constexpr int writes_per_reduce = pack_factor / values_per_reduce;

  size_t offset = index.x + grid_dim.x * size_t(index.y);
  size_t in_index = offset * values_per_reduce;

  float w_thread[values_per_reduce];
  float local_abs_sum = 0;

#pragma clang loop unroll(full)
  for (int i = 0; i < values_per_reduce; i++) {
    float val = w[in_index + i];
    w_thread[i] = val;
    local_abs_sum += abs(val);
  }

  // Each simdgroup covers exactly one group (values_per_reduce * SIMD_SIZE
  // == group_size), so summing every lane's partial abs-sum across the
  // simdgroup gives the group's total abs-sum directly.
  float scale = max(simd_sum(local_abs_sum) / float(group_size), eps);

  size_t gindex = in_index / group_size;
  if (in_index % group_size == 0) {
    scales[gindex] = static_cast<T>(scale);
  }

  // pack_factor (4, fixed) is never less than values_per_reduce (<= 4 for
  // the supported group sizes), so every lane always combines with its
  // neighbors via simd_shuffle_down rather than flushing a self-contained
  // byte on its own -- unlike affine's generic bits path, there is no
  // "flush now" case to handle here.
  uint8_t output = 0;
#pragma clang loop unroll(full)
  for (int i = 0; i < values_per_reduce; i++) {
    float shifted = round(clamp(w_thread[i] / scale, -1.0f, 1.0f)) + 1.0f;
    uint8_t val = static_cast<uint8_t>(shifted); // {-1,0,1} -> {0,1,2}
    output |= val << (bits * i);

#pragma clang loop unroll(full)
    for (int j = 1; j < writes_per_reduce; j++) {
      uint8_t sval = simd_shuffle_down(val, j);
      output |= static_cast<uint8_t>(sval)
          << (bits * (j * values_per_reduce + i));
    }
  }
  if (offset % writes_per_reduce == 0) {
    out[offset / writes_per_reduce] = output;
  }
}

template <typename T, const int group_size, const int bits>
[[kernel]] void ternary_dequantize(
    const device uint8_t* w [[buffer(0)]],
    const device T* scales [[buffer(1)]],
    device T* out [[buffer(3)]],
    uint2 index [[thread_position_in_grid]],
    uint2 grid_dim [[threads_per_grid]]) {
  static_assert(bits == 2, "ternary quantization requires bits == 2");
  constexpr int pack_factor = 8 / bits; // codes per byte

  size_t offset = index.x + grid_dim.x * size_t(index.y);
  size_t oindex = offset * pack_factor;
  size_t gindex = oindex / group_size;
  T scale = scales[gindex];

  out += oindex;

  uint val = w[offset];
#pragma clang loop unroll(full)
  for (int i = 0; i < pack_factor; i++) {
    uint8_t d = (val >> (bits * i)) & 0x03;
    out[i] = static_cast<T>(scale * (float(d) - 1.0f));
  }
}

// values_per_thread ternary codes, packed 4 per byte LSB-first (bits == 2
// fixed), decoded to signed {-1,0,1} via code - 1, multiply-accumulated
// against x_thread, and scaled once at the end -- same shape as fp
// quantized.h's own qdot, adapted for ternary's direct (non fp8-encoded)
// scale and 2-bit codes.
template <typename U, int values_per_thread>
inline U
ternary_qdot(const device uint8_t* w, const thread U* x_thread, U scale) {
  U accum = 0;
  constexpr int bytes = values_per_thread / 4;
#pragma clang loop unroll(full)
  for (int b = 0; b < bytes; b++) {
    uint8_t byte = w[b];
#pragma clang loop unroll(full)
    for (int j = 0; j < 4; j++) {
      uint8_t code = (byte >> (2 * j)) & 0x03;
      accum += x_thread[b * 4 + j] * (U(code) - U(1));
    }
  }
  return scale * accum;
}

// Same as ternary_qdot, but only reads/decodes the first N codes (ceil(N/4)
// bytes) instead of the full values_per_thread -- required for the K-tail
// block of ternary_qmv_impl below, where reading a full values_per_thread
// worth of packed weight bytes past a row's own K range could read past the
// end of the whole weight buffer for the very last output row (zero-padding
// x_thread alone isn't enough: it makes the arithmetic contribution zero,
// but does not stop the out-of-bounds *read* of w from happening).
template <typename U, int values_per_thread>
inline U ternary_qdot_safe(
    const device uint8_t* w,
    const thread U* x_thread,
    U scale,
    int N) {
  U accum = 0;
  int full_bytes = N / 4;
  int rem = N % 4;
  for (int b = 0; b < full_bytes; b++) {
    uint8_t byte = w[b];
    for (int j = 0; j < 4; j++) {
      uint8_t code = (byte >> (2 * j)) & 0x03;
      accum += x_thread[b * 4 + j] * (U(code) - U(1));
    }
  }
  if (rem > 0) {
    uint8_t byte = w[full_bytes];
    for (int j = 0; j < rem; j++) {
      uint8_t code = (byte >> (2 * j)) & 0x03;
      accum += x_thread[full_bytes * 4 + j] * (U(code) - U(1));
    }
  }
  return scale * accum;
}

template <typename T, typename U, int values_per_thread>
inline void ternary_load_vector(const device T* x, thread U* x_thread) {
#pragma clang loop unroll(full)
  for (int i = 0; i < values_per_thread; i++) {
    x_thread[i] = x[i];
  }
}

template <typename T, typename U, int values_per_thread>
inline void
ternary_load_vector_safe(const device T* x, thread U* x_thread, int N) {
  for (int i = 0; i < N; i++) {
    x_thread[i] = x[i];
  }
  for (int i = N; i < values_per_thread; i++) {
    x_thread[i] = 0;
  }
}

// Mirrors fp_qmv_impl (mlx/backend/metal/kernels/fp_quantized.h) -- the
// general, bounds-checked qmv: any K (via ternary_load_vector_safe/
// ternary_qdot_safe for the K-tail) and any N (via the two branches below --
// one for out_vec_size smaller than a whole tile, one that shifts the last
// tile back to avoid a partial-tile write), unlike ternary_qmv_fast_impl's
// exact-multiple requirements. Same non-batched-only scope as
// ternary_qmv_fast_impl.
template <typename T, int group_size, int bits>
METAL_FUNC void ternary_qmv_impl(
    const device uint32_t* w,
    const device T* scales,
    const device T* x,
    device T* y,
    const constant int& in_vec_size,
    const constant int& out_vec_size,
    uint3 tid [[threadgroup_position_in_grid]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  static_assert(bits == 2, "ternary quantization requires bits == 2");
  constexpr int num_simdgroups = 2;
  constexpr int results_per_simdgroup = 4;
  constexpr int packs_per_thread = 1;
  constexpr int pack_factor = 32 / bits; // codes per uint32 word
  constexpr int bytes_per_pack = 4; // bytes per uint32 word

  constexpr int values_per_thread = pack_factor * packs_per_thread;
  constexpr int block_size = values_per_thread * SIMD_SIZE;
  constexpr int scale_step_per_thread = group_size / values_per_thread;

  const device uint8_t* ws = (const device uint8_t*)w;

  typedef float U;

  thread U x_thread[values_per_thread];
  thread U result[results_per_simdgroup] = {0};

  const int in_vec_size_w = in_vec_size * bytes_per_pack / pack_factor;
  const int in_vec_size_g = in_vec_size / group_size;
  const int out_row = tid.y * (num_simdgroups * results_per_simdgroup) +
      simd_gid * results_per_simdgroup;
  const int used_out_row = min(out_vec_size - results_per_simdgroup, out_row);

  if (out_row >= out_vec_size) {
    return;
  }

  if (out_vec_size < (num_simdgroups * results_per_simdgroup)) {
    ws +=
        out_row * in_vec_size_w + simd_lid * packs_per_thread * bytes_per_pack;
    scales += out_row * in_vec_size_g + simd_lid / scale_step_per_thread;
    x += tid.x * in_vec_size + simd_lid * values_per_thread;
    y += tid.x * out_vec_size + out_row;

    int k = 0;
    for (; k < in_vec_size - block_size; k += block_size) {
      ternary_load_vector<T, U, values_per_thread>(x, x_thread);

      for (int row = 0;
           row < results_per_simdgroup && out_row + row < out_vec_size;
           row++) {
        auto wl = (const device uint8_t*)(ws + row * in_vec_size_w);
        const device T* sl = scales + row * in_vec_size_g;

        U s = static_cast<U>(sl[0]);
        result[row] += ternary_qdot<U, values_per_thread>(wl, x_thread, s);
      }

      ws += block_size * bytes_per_pack / pack_factor;
      scales += block_size / group_size;
      x += block_size;
    }
    const int remaining = clamp(
        static_cast<int>(in_vec_size - k - simd_lid * values_per_thread),
        0,
        values_per_thread);
    if (remaining > 0) {
      ternary_load_vector_safe<T, U, values_per_thread>(x, x_thread, remaining);

      for (int row = 0;
           row < results_per_simdgroup && out_row + row < out_vec_size;
           row++) {
        auto wl = (const device uint8_t*)(ws + row * in_vec_size_w);
        const device T* sl = scales + row * in_vec_size_g;

        U s = static_cast<U>(sl[0]);
        result[row] +=
            ternary_qdot_safe<U, values_per_thread>(wl, x_thread, s, remaining);
      }
    }

    for (int row = 0;
         row < results_per_simdgroup && out_row + row < out_vec_size;
         row++) {
      result[row] = simd_sum(result[row]);
      if (simd_lid == 0) {
        y[row] = static_cast<T>(result[row]);
      }
    }
  } else {
    ws += used_out_row * in_vec_size_w +
        simd_lid * packs_per_thread * bytes_per_pack;
    scales += used_out_row * in_vec_size_g + simd_lid / scale_step_per_thread;
    x += tid.x * in_vec_size + simd_lid * values_per_thread;
    y += tid.x * out_vec_size + used_out_row;

    int k = 0;
    for (; k < in_vec_size - block_size; k += block_size) {
      ternary_load_vector<T, U, values_per_thread>(x, x_thread);

      for (int row = 0; row < results_per_simdgroup; row++) {
        auto wl = (const device uint8_t*)(ws + row * in_vec_size_w);
        const device T* sl = scales + row * in_vec_size_g;

        U s = static_cast<U>(sl[0]);
        result[row] += ternary_qdot<U, values_per_thread>(wl, x_thread, s);
      }

      ws += block_size * bytes_per_pack / pack_factor;
      scales += block_size / group_size;
      x += block_size;
    }
    const int remaining = clamp(
        static_cast<int>(in_vec_size - k - simd_lid * values_per_thread),
        0,
        values_per_thread);
    if (remaining > 0) {
      ternary_load_vector_safe<T, U, values_per_thread>(x, x_thread, remaining);

      for (int row = 0; row < results_per_simdgroup; row++) {
        auto wl = (const device uint8_t*)(ws + row * in_vec_size_w);
        const device T* sl = scales + row * in_vec_size_g;

        U s = static_cast<U>(sl[0]);
        result[row] +=
            ternary_qdot_safe<U, values_per_thread>(wl, x_thread, s, remaining);
      }
    }
    for (int row = 0; row < results_per_simdgroup; row++) {
      result[row] = simd_sum(result[row]);
      if (simd_lid == 0) {
        y[row] = static_cast<T>(result[row]);
      }
    }
  }
}

template <typename T, int group_size, int bits>
[[kernel]] void ternary_qmv(
    const device uint32_t* w [[buffer(0)]],
    const device T* scales [[buffer(1)]],
    const device T* x [[buffer(2)]],
    device T* y [[buffer(3)]],
    const constant int& in_vec_size [[buffer(4)]],
    const constant int& out_vec_size [[buffer(5)]],
    uint3 tid [[threadgroup_position_in_grid]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  ternary_qmv_impl<T, group_size, bits>(
      w, scales, x, y, in_vec_size, out_vec_size, tid, simd_gid, simd_lid);
}

// Mirrors fp_qmv_fast_impl (mlx/backend/metal/kernels/fp_quantized.h) --
// same threading model (2 simdgroups/threadgroup, 4 results/simdgroup,
// simd_lid-based per-lane weight/activation offsetting, simd_sum reduction)
// -- but reads scale as a direct T value (no dequantize_scale decode) and
// non-batched only (no adjust_matrix_offsets/x_batch_ndims machinery):
// mlx::quantized_matmul only ever calls this for w.ndim() == 2.
template <typename T, int group_size, int bits>
METAL_FUNC void ternary_qmv_fast_impl(
    const device uint32_t* w,
    const device T* scales,
    const device T* x,
    device T* y,
    const constant int& in_vec_size,
    const constant int& out_vec_size,
    uint3 tid [[threadgroup_position_in_grid]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  static_assert(bits == 2, "ternary quantization requires bits == 2");
  constexpr int packs_per_thread = 2;
  constexpr int num_simdgroups = 2;
  constexpr int results_per_simdgroup = 4;
  constexpr int pack_factor = 32 / bits; // codes per uint32 word
  constexpr int bytes_per_pack = 4; // bytes per uint32 word
  constexpr int values_per_thread = pack_factor * packs_per_thread;
  constexpr int block_size = values_per_thread * SIMD_SIZE;
  constexpr int scale_step_per_thread = group_size / values_per_thread;
  static_assert(
      scale_step_per_thread >= 1,
      "group_size must be at least pack_factor * packs_per_thread * SIMD_SIZE / SIMD_SIZE");

  const device uint8_t* ws = (const device uint8_t*)w;

  typedef float U;
  thread U x_thread[values_per_thread];
  thread U result[results_per_simdgroup] = {0};

  const int in_vec_size_w = in_vec_size * bytes_per_pack / pack_factor;
  const int in_vec_size_g = in_vec_size / group_size;
  const int out_row = tid.y * (num_simdgroups * results_per_simdgroup) +
      simd_gid * results_per_simdgroup;

  ws += out_row * in_vec_size_w + simd_lid * packs_per_thread * bytes_per_pack;
  scales += out_row * in_vec_size_g + simd_lid / scale_step_per_thread;
  x += tid.x * in_vec_size + simd_lid * values_per_thread;
  y += tid.x * out_vec_size + out_row;

  for (int k = 0; k < in_vec_size; k += block_size) {
#pragma clang loop unroll(full)
    for (int i = 0; i < values_per_thread; i++) {
      x_thread[i] = x[i];
    }

    for (int row = 0; row < results_per_simdgroup; row++) {
      auto wl = (const device uint8_t*)(ws + row * in_vec_size_w);
      const device T* sl = scales + row * in_vec_size_g;

      U s = static_cast<U>(sl[0]);
      result[row] += ternary_qdot<U, values_per_thread>(wl, x_thread, s);
    }

    ws += block_size * bytes_per_pack / pack_factor;
    scales += block_size / group_size;
    x += block_size;
  }

  for (int row = 0; row < results_per_simdgroup; row++) {
    result[row] = simd_sum(result[row]);
    if (simd_lid == 0) {
      y[row] = static_cast<T>(result[row]);
    }
  }
}

template <typename T, int group_size, int bits>
[[kernel]] void ternary_qmv_fast(
    const device uint32_t* w [[buffer(0)]],
    const device T* scales [[buffer(1)]],
    const device T* x [[buffer(2)]],
    device T* y [[buffer(3)]],
    const constant int& in_vec_size [[buffer(4)]],
    const constant int& out_vec_size [[buffer(5)]],
    uint3 tid [[threadgroup_position_in_grid]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  ternary_qmv_fast_impl<T, group_size, bits>(
      w, scales, x, y, in_vec_size, out_vec_size, tid, simd_gid, simd_lid);
}

// values_per_thread ternary codes (packed 4 per byte, LSB-first) decoded
// and accumulated as an OUTER product: one x scalar times each of
// values_per_thread weight codes, into that many result accumulators.
// Mirrors quantized.h's own qouter, minus the bias term ternary doesn't
// have.
template <typename U, int values_per_thread>
inline void
ternary_qouter(const thread uint8_t* w, U x, U scale, thread U* result) {
  constexpr int bytes = values_per_thread / 4;
#pragma clang loop unroll(full)
  for (int b = 0; b < bytes; b++) {
    uint8_t byte = w[b];
#pragma clang loop unroll(full)
    for (int j = 0; j < 4; j++) {
      uint8_t code = (byte >> (2 * j)) & 0x03;
      result[b * 4 + j] += x * scale * (U(code) - U(1));
    }
  }
}

// Mirrors qvm_impl (mlx/backend/metal/kernels/quantized.h) -- x @ w with w
// stored (K, N) (transpose == false), one x scalar per lane per block,
// values_per_thread output columns decoded and accumulated per lane, then
// simd_sum'd across the group. Non-batched only, like ternary_qmv_fast_impl
// above: mlx::quantized_matmul only calls this for w.ndim() == 2. in_vec_stride
// is separate from in_vec_size only for the split-K variant below (identical
// to it otherwise), matching qvm_impl's own parameterization.
template <typename T, int group_size, int bits>
METAL_FUNC void ternary_qvm_impl(
    const device uint32_t* w,
    const device T* scales,
    const device T* x,
    device T* y,
    const int in_vec_size,
    const int out_vec_size,
    const int in_vec_stride,
    uint3 tid [[threadgroup_position_in_grid]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  static_assert(bits == 2, "ternary quantization requires bits == 2");
  constexpr int num_simdgroups = 2;
  constexpr int pack_factor = 32 / bits; // codes per uint32 word
  constexpr int tn = 32 / pack_factor; // uint32 words per thread
  constexpr int block_size = SIMD_SIZE;
  constexpr int values_per_thread = tn * pack_factor;

  typedef float U;
  typedef struct {
    uint32_t wi[tn];
  } vec_w;

  thread vec_w w_local;
  thread U result[values_per_thread] = {0};
  thread U scale = 1;
  thread U x_local = 0;

  const int out_vec_size_w = out_vec_size / pack_factor;
  const int out_vec_size_g = out_vec_size / group_size;
  int out_col = values_per_thread * (tid.y * num_simdgroups + simd_gid);
  const device uint32_t* ws =
      w + out_col / pack_factor + simd_lid * out_vec_size_w;
  scales += out_col / group_size + simd_lid * out_vec_size_g;
  x += tid.x * in_vec_stride + simd_lid;
  y += tid.x * out_vec_size + out_col;

  if (out_col >= out_vec_size) {
    return;
  }

  int remaining = in_vec_size % block_size;
  if (remaining == 0) {
    for (int i = 0; i < in_vec_size; i += block_size) {
      x_local = *x;
      scale = static_cast<U>(*scales);
      w_local = *((const device vec_w*)ws);
      ternary_qouter<U, values_per_thread>(
          (const thread uint8_t*)&w_local, x_local, scale, result);

      x += block_size;
      scales += block_size * out_vec_size_g;
      ws += block_size * out_vec_size_w;
    }
  } else {
    for (int i = block_size; i < in_vec_size; i += block_size) {
      x_local = *x;
      scale = static_cast<U>(*scales);
      w_local = *((const device vec_w*)ws);
      ternary_qouter<U, values_per_thread>(
          (const thread uint8_t*)&w_local, x_local, scale, result);

      x += block_size;
      scales += block_size * out_vec_size_g;
      ws += block_size * out_vec_size_w;
    }
    if (static_cast<int>(simd_lid) < remaining) {
      x_local = *x;
      scale = static_cast<U>(*scales);
      w_local = *((const device vec_w*)ws);
    } else {
      x_local = 0;
      scale = 0;
    }
    ternary_qouter<U, values_per_thread>(
        (const thread uint8_t*)&w_local, x_local, scale, result);
  }

#pragma clang loop unroll(full)
  for (int k = 0; k < values_per_thread; k++) {
    result[k] = simd_sum(result[k]);
  }

  if (simd_lid == 0) {
#pragma clang loop unroll(full)
    for (int k = 0; k < values_per_thread; k++) {
      y[k] = static_cast<T>(result[k]);
    }
  }
}

template <typename T, int group_size, int bits>
[[kernel]] void ternary_qvm(
    const device uint32_t* w [[buffer(0)]],
    const device T* scales [[buffer(1)]],
    const device T* x [[buffer(2)]],
    device T* y [[buffer(3)]],
    const constant int& in_vec_size [[buffer(4)]],
    const constant int& out_vec_size [[buffer(5)]],
    uint3 tid [[threadgroup_position_in_grid]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  ternary_qvm_impl<T, group_size, bits>(
      w,
      scales,
      x,
      y,
      in_vec_size,
      out_vec_size,
      in_vec_size,
      tid,
      simd_gid,
      simd_lid);
}

// Ternary tiled GEMM (large-M matmul), transpose == true, non-batched
// weights. Mirrors quantized.h's QuantizedBlockLoader/qmm_t_impl/
// affine_qmm_t almost line-for-line, minus everything bias-related (no
// bias field/ctor-param/next()-increment, dequantize writes ternary
// {-1,0,1} codes directly instead of affine's per-subcode-scale trick)
// and minus the batched-weight adjust_matrix_offsets machinery (same
// non-batched-only scope as every other kernel in this file). qmm_t_impl
// itself has no K-tail loop at all -- it assumes K is an exact multiple
// of BK(32), which mx.quantize's own group_size%K==0 requirement
// guarantees here too, since group_size is always a multiple of 32.
template <
    typename T,
    short BROWS,
    short BCOLS,
    short dst_ld,
    short reduction_dim,
    short tgp_size,
    short group_size,
    short bits>
struct TernaryQuantizedBlockLoader {
  static_assert(bits == 2, "ternary quantization requires bits == 2");
  static_assert(
      BCOLS <= group_size,
      "The group size should be larger than the columns");
  static_assert(
      group_size % BCOLS == 0,
      "The group size should be divisible by the columns");

  MLX_MTL_CONST short pack_factor = 8 / bits; // codes per byte
  MLX_MTL_CONST short bytes_per_pack = 1; // bytes per pack_factor codes
  MLX_MTL_CONST short BCOLS_PACKED = BCOLS / pack_factor;
  MLX_MTL_CONST short n_reads =
      (BCOLS_PACKED * BROWS < tgp_size) ? 1 : (BCOLS_PACKED * BROWS) / tgp_size;
  MLX_MTL_CONST short group_steps = group_size / BCOLS;

  const int src_ld;
  const int tile_stride;
  short group_step_cnt;
  const int group_stride;

  const short thread_idx;
  const short bi;
  const short bj;

  threadgroup T* dst;
  const device uint8_t* src;
  const device T* scales;

  TernaryQuantizedBlockLoader(
      const device uint8_t* src_,
      const device T* scales_,
      const int src_ld_,
      threadgroup T* dst_,
      ushort simd_group_id [[simdgroup_index_in_threadgroup]],
      ushort simd_lane_id [[thread_index_in_simdgroup]])
      : src_ld(src_ld_),
        tile_stride(
            reduction_dim ? BCOLS_PACKED * bytes_per_pack
                          : BROWS * src_ld * bytes_per_pack / pack_factor),
        group_step_cnt(0),
        group_stride(BROWS * src_ld / group_size),
        thread_idx(simd_group_id * 32 + simd_lane_id),
        bi(n_reads * thread_idx / BCOLS_PACKED),
        bj((n_reads * thread_idx) % BCOLS_PACKED),
        dst(dst_ + bi * dst_ld + bj * pack_factor),
        src(src_ + bi * src_ld * bytes_per_pack / pack_factor +
            bj * bytes_per_pack),
        scales(scales_ + bi * src_ld / group_size) {}

  void load_unsafe() const {
    if (BCOLS_PACKED * BROWS < tgp_size && bi >= BROWS) {
      return;
    }
    T scale = *scales;
    for (int i = 0; i < n_reads; i++) {
      uint8_t byte = src[i * bytes_per_pack];
      threadgroup T* d = dst + i * pack_factor;
#pragma clang loop unroll(full)
      for (int j = 0; j < 4; j++) {
        uint8_t code = (byte >> (2 * j)) & 0x03;
        d[j] = scale * (T(code) - T(1));
      }
    }
  }

  void load_safe(short2 src_tile_dim) const {
    if (BCOLS_PACKED * BROWS < tgp_size && bi >= BROWS) {
      return;
    }

    if (reduction_dim == 1 && bi >= src_tile_dim.x) {
      for (int i = 0; i < n_reads * pack_factor; i++) {
        dst[i] = T(0);
      }
      return;
    }

    if (reduction_dim == 0 && bi >= src_tile_dim.y) {
      for (int i = 0; i < n_reads * pack_factor; i++) {
        dst[i] = T(0);
      }
      return;
    }

    T scale = *scales;
    for (int i = 0; i < n_reads; i++) {
      uint8_t byte = src[i * bytes_per_pack];
      threadgroup T* d = dst + i * pack_factor;
#pragma clang loop unroll(full)
      for (int j = 0; j < 4; j++) {
        uint8_t code = (byte >> (2 * j)) & 0x03;
        d[j] = scale * (T(code) - T(1));
      }
    }
  }

  void next() {
    src += tile_stride;
    if (reduction_dim == 1) {
      if (group_steps > 1) {
        group_step_cnt++;
        if (group_step_cnt == group_steps) {
          group_step_cnt = 0;
          scales++;
        }
      } else {
        scales++;
      }
    } else {
      scales += group_stride;
    }
  }
};

template <
    typename T,
    const int group_size,
    const int bits,
    const bool aligned_N,
    const int BM = 32,
    const int BK = 32,
    const int BN = 32>
METAL_FUNC void ternary_qmm_t_impl(
    const device uint32_t* w,
    const device T* scales,
    const device T* x,
    device T* y,
    threadgroup T* Xs,
    threadgroup T* Ws,
    const constant int& K,
    const constant int& N,
    const constant int& M,
    uint3 tid [[threadgroup_position_in_grid]],
    uint lid [[thread_index_in_threadgroup]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  static_assert(bits == 2, "ternary quantization requires bits == 2");
  static_assert(BK >= SIMD_SIZE, "BK should be larger than SIMD_SIZE");
  static_assert(BK % SIMD_SIZE == 0, "BK should be divisible by SIMD_SIZE");

  (void)lid;

  constexpr int WM = 2;
  constexpr int WN = 2;
  constexpr int pack_factor = 8 / bits; // codes per byte
  constexpr int bytes_per_pack = 1;

  constexpr int BK_padded = (BK + 16 / sizeof(T));

  using mma_t = mlx::steel::
      BlockMMA<T, T, BM, BN, BK, WM, WN, false, true, BK_padded, BK_padded>;
  using loader_x_t =
      mlx::steel::BlockLoader<T, BM, BK, BK_padded, 1, WM * WN * SIMD_SIZE>;
  using loader_w_t = TernaryQuantizedBlockLoader<
      T,
      BN,
      BK,
      BK_padded,
      1,
      WM * WN * SIMD_SIZE,
      group_size,
      bits>;

  const int K_w = K * bytes_per_pack / pack_factor;
  const int K_g = K / group_size;
  const int y_row = tid.y * BM;
  const int y_col = tid.x * BN;

  auto wl = (const device uint8_t*)w;

  x += y_row * static_cast<int64_t>(K);
  wl += y_col * K_w;
  scales += y_col * K_g;
  y += y_row * static_cast<int64_t>(N) + y_col;

  const short num_els = min(BM, M - y_row);
  const short num_outs = min(BN, N - y_col);
  loader_x_t loader_x(x, K, Xs, simd_gid, simd_lid);
  loader_w_t loader_w(wl, scales, K, Ws, simd_gid, simd_lid);
  mma_t mma_op(simd_gid, simd_lid);

  if (num_els < BM) {
    if (!aligned_N && num_outs < BN) {
      for (int k = 0; k < K; k += BK) {
        threadgroup_barrier(mem_flags::mem_threadgroup);
        loader_x.load_safe(short2(BK, num_els));
        loader_w.load_safe(short2(BK, num_outs));
        threadgroup_barrier(mem_flags::mem_threadgroup);
        mma_op.mma(Xs, Ws);
        loader_x.next();
        loader_w.next();
      }
    } else {
      for (int k = 0; k < K; k += BK) {
        threadgroup_barrier(mem_flags::mem_threadgroup);
        loader_x.load_safe(short2(BK, num_els));
        loader_w.load_unsafe();
        threadgroup_barrier(mem_flags::mem_threadgroup);
        mma_op.mma(Xs, Ws);
        loader_x.next();
        loader_w.next();
      }
    }
  } else {
    if (!aligned_N && num_outs < BN) {
      for (int k = 0; k < K; k += BK) {
        threadgroup_barrier(mem_flags::mem_threadgroup);
        loader_x.load_unsafe();
        loader_w.load_safe(short2(BK, num_outs));
        threadgroup_barrier(mem_flags::mem_threadgroup);
        mma_op.mma(Xs, Ws);
        loader_x.next();
        loader_w.next();
      }
    } else {
      for (int k = 0; k < K; k += BK) {
        threadgroup_barrier(mem_flags::mem_threadgroup);
        loader_x.load_unsafe();
        loader_w.load_unsafe();
        threadgroup_barrier(mem_flags::mem_threadgroup);
        mma_op.mma(Xs, Ws);
        loader_x.next();
        loader_w.next();
      }
    }
  }

  threadgroup_barrier(mem_flags::mem_threadgroup);
  if (num_els < BM || num_outs < BN) {
    mma_op.store_result_safe(y, N, short2(num_outs, num_els));
  } else {
    mma_op.store_result(y, N);
  }
}

template <
    typename T,
    const int group_size,
    const int bits,
    const bool aligned_N,
    const int BM = 32,
    const int BK = 32,
    const int BN = 32>
[[kernel]] void ternary_qmm_t(
    const device uint32_t* w [[buffer(0)]],
    const device T* scales [[buffer(1)]],
    const device T* x [[buffer(2)]],
    device T* y [[buffer(3)]],
    const constant int& K [[buffer(4)]],
    const constant int& N [[buffer(5)]],
    const constant int& M [[buffer(6)]],
    uint3 tid [[threadgroup_position_in_grid]],
    uint lid [[thread_index_in_threadgroup]],
    uint simd_gid [[simdgroup_index_in_threadgroup]],
    uint simd_lid [[thread_index_in_simdgroup]]) {
  (void)lid;
  constexpr int BK_padded = (BK + 16 / sizeof(T));

  threadgroup T Xs[BM * BK_padded];
  threadgroup T Ws[BN * BK_padded];

  ternary_qmm_t_impl<T, group_size, bits, aligned_N, BM, BK, BN>(
      w, scales, x, y, Xs, Ws, K, N, M, tid, lid, simd_gid, simd_lid);
}

inline uint hash_rand(uint seed, uint idx) {
  uint h = seed ^ idx;
  h ^= h >> 16;
  h *= 0x85ebca6bU;
  h ^= h >> 13;
  h *= 0xc2b2ae35U;
  h ^= h >> 16;
  return h;
}

inline float hash_randf(uint seed, uint idx) {
  return float(hash_rand(seed, idx)) / float(0xffffffffU);
}

template <typename T, const int group_size, const int bits>
[[kernel]] void ternary_maybequant(
    const device T* w [[buffer(0)]],
    device uint8_t* out [[buffer(1)]],
    device T* scales [[buffer(2)]],
    const constant float& prob [[buffer(3)]],
    const constant uint& seed [[buffer(4)]],
    uint2 index [[thread_position_in_grid]],
    uint2 grid_dim [[threads_per_grid]]) {
  static_assert(bits == 2);
  static_assert(group_size % SIMD_SIZE == 0);

  constexpr float eps = 1e-7;
  constexpr int pack_factor = 8 / bits;
  constexpr int values_per_reduce = group_size / SIMD_SIZE;
  constexpr int writes_per_reduce = pack_factor / values_per_reduce;

  size_t offset = index.x + grid_dim.x * size_t(index.y);
  size_t in_index = offset * values_per_reduce;

  float w_thread[values_per_reduce];
  float local_abs_sum = 0;

#pragma clang loop unroll(full)
  for (int i = 0; i < values_per_reduce; i++) {
    float val = w[in_index + i];
    float r = hash_randf(seed, in_index + i);
    float keep = r > prob ? val : 0.0f;
    w_thread[i] = keep;
    local_abs_sum += abs(keep);
  }

  float scale = max(simd_sum(local_abs_sum) / float(group_size), eps);

  size_t gindex = in_index / group_size;
  if (in_index % group_size == 0) {
    scales[gindex] = static_cast<T>(scale);
  }

  uint8_t output = 0;
#pragma clang loop unroll(full)
  for (int i = 0; i < values_per_reduce; i++) {
    float shifted = round(clamp(w_thread[i] / scale, -1.0f, 1.0f)) + 1.0f;
    uint8_t val = static_cast<uint8_t>(shifted);
    output |= val << (bits * i);

#pragma clang loop unroll(full)
    for (int j = 1; j < writes_per_reduce; j++) {
      uint8_t sval = simd_shuffle_down(val, j);
      output |= static_cast<uint8_t>(sval)
          << (bits * (j * values_per_reduce + i));
    }
  }
  if (offset % writes_per_reduce == 0) {
    out[offset / writes_per_reduce] = output;
  }
}

template <typename T, const int group_size, const int bits>
[[kernel]] void ternary_mergequant_matmul(
    const device T* w [[buffer(0)]],
    device T* scales [[buffer(1)]],
    const device T* x [[buffer(2)]],
    device T* y [[buffer(3)]],
    const constant int& K [[buffer(4)]],
    const constant int& N [[buffer(5)]],
    uint tid [[thread_position_in_grid]]) {
  static_assert(bits == 2);

  int n = tid;
  if (n >= N)
    return;

  constexpr float eps = 1e-7;
  constexpr int SIMD = SIMD_SIZE;

  float scale = 0;
  float local_abs_sum = 0;
  int groups = K / group_size;

  int row = tid / N;
  int col = tid % N;

  float accum = 0;
  const device T* wx = w + row * K;
  const device T* xx = x + row * K;

  for (int g = 0; g < groups; g++) {
    local_abs_sum = 0;
    for (int j = 0; j < group_size; j++) {
      local_abs_sum += abs(wx[g * group_size + j]);
    }
    scale = max(local_abs_sum / float(group_size), eps);

    for (int j = 0; j < group_size; j += 4) {
      float wv[4], xv[4];
      for (int s = 0; s < 4; s++) {
        int jj = g * group_size + j + s;
        float raw = wx[jj];
        float q = round(clamp(raw / scale, -1.0f, 1.0f));
        wv[s] = q * scale;
        xv[s] = xx[jj];
      }
      accum += wv[0] * xv[0] + wv[1] * xv[1] + wv[2] * xv[2] + wv[3] * xv[3];
    }
  }

  y[tid] = static_cast<T>(accum);
}

template <typename T, const int group_size, const int bits>
[[kernel]] void ternary_maybequant_matmul(
    const device T* w [[buffer(0)]],
    device T* scales [[buffer(1)]],
    const device T* x [[buffer(2)]],
    device T* y [[buffer(3)]],
    const constant int& K [[buffer(4)]],
    const constant int& N [[buffer(5)]],
    const constant float& prob [[buffer(6)]],
    const constant uint& seed [[buffer(7)]],
    uint tid [[thread_position_in_grid]]) {
  static_assert(bits == 2);

  if (tid >= N)
    return;

  constexpr float eps = 1e-7;
  int row = tid / N;
  int col = tid % N;

  float accum = 0;
  const device T* wx = w + row * K;
  const device T* xx = x + row * K;

  for (int g = 0; g < K / group_size; g++) {
    float local_abs_sum = 0;
    for (int j = 0; j < group_size; j++) {
      int jj = g * group_size + j;
      float raw = wx[jj];
      float r = hash_randf(seed, jj);
      local_abs_sum += r > prob ? abs(raw) : 0.0f;
    }
    float scale_val = max(local_abs_sum / float(group_size), eps);

    for (int j = 0; j < group_size; j += 4) {
      float wv[4], xv[4];
      for (int s = 0; s < 4; s++) {
        int jj = g * group_size + j + s;
        float raw = wx[jj];
        float r = hash_randf(seed, jj);
        float keep = r > prob ? raw : 0.0f;
        float q = round(clamp(keep / scale_val, -1.0f, 1.0f));
        wv[s] = q * scale_val;
        xv[s] = xx[jj];
      }
      accum += wv[0] * xv[0] + wv[1] * xv[1] + wv[2] * xv[2] + wv[3] * xv[3];
    }
  }

  y[tid] = static_cast<T>(accum);
}
