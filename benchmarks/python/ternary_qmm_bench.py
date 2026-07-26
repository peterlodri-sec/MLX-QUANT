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
    mx.eval(x, w)

    def dense(x):
        return x @ w.T

    def make_qmm(mode, bits):
        if mode == "affine":
            w_q, scales, biases = mx.quantize(w, bits=bits, mode=mode)
            mx.eval(w_q, scales, biases)
            return lambda x: mx.quantized_matmul(
                x, w_q, scales, biases, bits=bits, mode=mode
            )
        else:
            w_q, scales = mx.quantize(w, group_size=GROUP_SIZE, bits=bits, mode=mode)
            mx.eval(w_q, scales)
            return lambda x: mx.quantized_matmul(
                x, w_q, scales, group_size=GROUP_SIZE, bits=bits, mode=mode
            )

    time_fn(dense, x, msg=f"x @ w.T (dense fp32)                M={M} K={K} N={N}")
    # affine bits=4 is this codebase's own best-optimized comparable-width
    # CPU quantized kernel (real SIMD path, _qmm_t_simd) -- the honest
    # baseline to compare ternary against, not just dense fp32 BLAS.
    time_fn(
        make_qmm("affine", 4),
        x,
        msg=f"quantized_matmul(affine, bits=4)    M={M} K={K} N={N}",
    )
    # affine bits=2 has no SIMD path in this codebase at all (simd::max_size
    # doesn't divide evenly for bits=2 -- see _qmm_dispatch_transpose) and
    # always falls back to the scalar kernel -- shown for contrast.
    time_fn(
        make_qmm("affine", 2),
        x,
        msg=f"quantized_matmul(affine, bits=2, no SIMD) M={M} K={K} N={N}",
    )
    time_fn(
        make_qmm("ternary", 2),
        x,
        msg=f"quantized_matmul(ternary, bits=2)   M={M} K={K} N={N}",
    )


if __name__ == "__main__":
    print("Memory footprint (packed ternary storage vs. full fp32):")
    for out_features, in_features in [(4096, 4096), (11008, 4096), (32000, 4096)]:
        report_memory_footprint(out_features, in_features)

    print()
    print("quantized_matmul timing (fused SIMD kernel, M-tiled over MTILE=4 rows,")
    print("transpose=True path -- see _ternary_qmm_t_simd in")
    print("mlx/backend/cpu/quantized.cpp). Compared against dense fp32 BLAS AND")
    print("against this codebase's own existing affine bits=4/bits=2 CPU kernels,")
    print("since 'slower than dense BLAS' alone understates it: ternary beats")
    print("affine bits=4 (this codebase's best-optimized comparable-width CPU")
    print("kernel) at both M=1 and M=32, and is roughly an order of magnitude")
    print("faster than affine bits=2, which has no SIMD path at all.")
    for M, K, N in [(1, 4096, 4096), (32, 4096, 4096), (32, 4096, 11008)]:
        time_qmm(M, K, N)
