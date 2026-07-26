# Copyright © 2026 8b-is

import mlx.core as mx
from time_utils import time_fn

# Ternary (mode="ternary") is a native, packed 2-bit-per-weight quantization
# format -- unlike python/mlx/nn/layers/bitlinear.py's BitLinear, which
# keeps full-precision weights and only *simulates* quantization for
# training. This is CPU-only for now (see mx.quantize's docstring); there
# is no Metal/CUDA kernel yet.
mx.set_default_device(mx.cpu)

GROUP_SIZE = 64
BITS = 2


def report_memory_footprint(out_features, in_features):
    w = mx.random.normal((out_features, in_features))
    w_q, scales = mx.quantize(w, group_size=GROUP_SIZE, bits=BITS, mode="ternary")
    mx.eval(w_q, scales)

    full_bytes = w.nbytes
    packed_bytes = w_q.nbytes + scales.nbytes
    ratio = full_bytes / packed_bytes
    print(
        f"({out_features}, {in_features}) fp32: {full_bytes / 1e6:8.2f} MB   "
        f"ternary packed: {packed_bytes / 1e6:8.2f} MB   ratio: {ratio:5.2f}x"
    )


def time_qmm(M, K, N):
    mx.random.seed(0)
    x = mx.random.normal((M, K))
    w = mx.random.normal((N, K))
    w_full = w  # dense reference weight, same values modulo quantization
    w_q, scales = mx.quantize(w, group_size=GROUP_SIZE, bits=BITS, mode="ternary")
    mx.eval(x, w_full, w_q, scales)

    def dense(x):
        return x @ w_full.T

    def quantized(x):
        return mx.quantized_matmul(
            x, w_q, scales, group_size=GROUP_SIZE, bits=BITS, mode="ternary"
        )

    time_fn(dense, x, msg=f"x @ w.T (dense fp32)     M={M} K={K} N={N}")
    time_fn(quantized, x, msg=f"quantized_matmul(ternary) M={M} K={K} N={N}")


if __name__ == "__main__":
    print("Memory footprint (packed ternary storage vs. full fp32):")
    for out_features, in_features in [(4096, 4096), (11008, 4096), (32000, 4096)]:
        report_memory_footprint(out_features, in_features)

    print()
    print("quantized_matmul timing (unpack-then-BLAS-matmul CPU kernel, ")
    print("not yet a fused/SIMD kernel -- see mlx/backend/cpu/quantized.cpp):")
    for M, K, N in [(1, 4096, 4096), (32, 4096, 4096), (32, 4096, 11008)]:
        time_qmm(M, K, N)
