# Copyright © 2026 8b-is

import mlx.core as mx
from time_utils import time_fn

# GPU counterpart to ternary_qmm_bench.py (CPU). Exercises every fused
# ternary GPU kernel path (see mlx/backend/metal/kernels/ternary_quantized.h
# and the dispatch gating in mlx/ops.cpp's quantized_matmul):
#   - ternary_qmv_fast: transpose=True, non-batched, N%8==0, K%1024==0
#   - ternary_qmv:      transpose=True, non-batched, general K/N
#   - ternary_qvm:      transpose=False, non-batched
#   - ternary_qmm_t:    transpose=True, non-batched, M>=32 (tiled GEMM)
# plus the compose fallback (dequantize + dense matmul) they each replace,
# and dense fp32 matmul as the model-agnostic reference point.
mx.set_default_device(mx.gpu)

GROUP_SIZE = 64
BITS = 2


def compose(x, w_q, scales, transpose):
    w_dense = mx.dequantize(
        w_q, scales, group_size=GROUP_SIZE, bits=BITS, mode="ternary"
    )
    return x @ (w_dense.T if transpose else w_dense)


def bench_shape(M, K, N, transpose, label):
    mx.random.seed(0)
    x = mx.random.normal((M, K))
    w_shape = (N, K) if transpose else (K, N)
    w = mx.random.normal(w_shape)
    w_q, scales = mx.quantize(w, group_size=GROUP_SIZE, bits=BITS, mode="ternary")
    mx.eval(x, w, w_q, scales)

    def fused(x):
        return mx.quantized_matmul(
            x,
            w_q,
            scales,
            group_size=GROUP_SIZE,
            bits=BITS,
            mode="ternary",
            transpose=transpose,
        )

    def composed(x):
        return compose(x, w_q, scales, transpose)

    def dense(x):
        return (x @ w.T) if transpose else (x @ w)

    print(f"--- {label}: M={M} K={K} N={N} transpose={transpose} ---")
    time_fn(
        fused, x, msg="fused (ternary_qmv_fast/qmv/qvm/qmm_t, whichever gates match)"
    )
    time_fn(composed, x, msg="compose (dequantize + dense matmul)")
    time_fn(dense, x, msg="dense fp32 matmul (reference, not quantized)")


if __name__ == "__main__":
    if not mx.metal.is_available():
        raise SystemExit("No Metal GPU available -- this benchmark is GPU-only.")

    print("ternary_qmv_fast (decode shape: M=1, N%8==0, K%1024==0)")
    bench_shape(1, 4096, 4096, True, "qmv_fast")
    bench_shape(1, 8192, 4096, True, "qmv_fast")
    print()

    print("ternary_qmv (general: doesn't meet qmv_fast's exact-multiple precondition)")
    bench_shape(1, 4096, 4096 + 8, True, "qmv (N not %1024-aligned-friendly)")
    bench_shape(8, 4032, 4096, True, "qmv (K not %1024)")
    print()

    print("ternary_qvm (transpose=False)")
    bench_shape(1, 4096, 4096, False, "qvm")
    bench_shape(8, 4096, 4096, False, "qvm")
    print()

    print("ternary_qmm_t (tiled GEMM, M>=32)")
    bench_shape(32, 4096, 4096, True, "qmm_t")
    bench_shape(64, 4096, 4096, True, "qmm_t")
    bench_shape(128, 4096, 4096, True, "qmm_t")
    bench_shape(256, 4096, 11008, True, "qmm_t (llama-mlp-ish shape)")
