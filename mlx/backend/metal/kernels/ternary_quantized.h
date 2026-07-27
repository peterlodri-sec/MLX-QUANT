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
inline U ternary_qdot(const device uint8_t* w, const thread U* x_thread, U scale) {
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
