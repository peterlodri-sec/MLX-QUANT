// Copyright © 2026 8b-is

// clang-format off
#include "mlx/backend/metal/kernels/utils.h"
#include "mlx/backend/metal/kernels/ternary_quantized.h"

#define instantiate_ternary_quantized(name, type, group_size, bits) \
  instantiate_kernel(                                               \
      "ternary_" #name "_" #type "_gs_" #group_size "_b_" #bits,    \
      ternary_ ## name,                                             \
      type,                                                         \
      group_size,                                                   \
      bits)

#define instantiate_ternary_quantized_funcs(type, group_size, bits) \
  instantiate_ternary_quantized(quantize, type, group_size, bits)   \
  instantiate_ternary_quantized(dequantize, type, group_size, bits) \
  instantiate_ternary_quantized(qmv_fast, type, group_size, bits)   \
  instantiate_ternary_quantized(qvm, type, group_size, bits)        \
  instantiate_ternary_quantized(qmv, type, group_size, bits)

#define instantiate_ternary_quantized_types(group_size, bits)      \
  instantiate_ternary_quantized_funcs(float, group_size, bits)     \
  instantiate_ternary_quantized_funcs(float16_t, group_size, bits) \
  instantiate_ternary_quantized_funcs(bfloat16_t, group_size, bits)

#define instantiate_ternary_quantized_all()  \
  instantiate_ternary_quantized_types(32, 2) \
  instantiate_ternary_quantized_types(64, 2) \
  instantiate_ternary_quantized_types(128, 2)

instantiate_ternary_quantized_all() // clang-format on
