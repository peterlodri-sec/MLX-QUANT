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
// This file intentionally only covers the standalone quantize/dequantize
// kernels, not a fused qmv/qmv_fast/qmv_wide/qmm matmul kernel family --
// mlx::quantized_matmul composes a correct GPU answer for ternary out of
// these plus the existing dense matmul instead (see mlx/ops.cpp), so no
// shape/dtype combination can reach a kernel name that was never written.

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
