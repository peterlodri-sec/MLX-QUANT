<!-- Supplementary v1.4.2 overview, placed next to the hero for convergence with
     the main README. Additive — does not replace ../README.md. -->

# MLX-QUANT

**MLX-QUANT** is 8b-is's fork of Apple's [MLX](https://github.com/ml-explore/mlx) that adds native **BitNet b1.58 ternary** ($\{-1, 0, +1\}$, $\approx 1.58$ bits/weight) quantization kernels for Apple Silicon across CPU and Metal GPU targets. Upstream MLX documentation applies to all existing framework features; this fork specifically introduces the native ternary path and execution routines.

## Why Ternary?

Constraining weights strictly to $\{-1, 0, +1\}$ turns floating-point matrix multiplication into simple element selection: pure addition, subtraction, and skipping. By eliminating floating-point multiplications during weight-matrix accumulation and achieving a theoretical storage density of $\log_2(3) \approx 1.58$ bits per weight, the BitNet b1.58 lineage significantly reduces memory bandwidth and memory footprint during inference and training.

## v1.4.2 Status: Fused vs. Composed / Deferred

### Fused Kernels
* **`gather_qmm` ternary**: Works on both CPU and Metal GPU, with gradients verified — composed from `dequantize` + the existing dense `gather_mm` op, not a dedicated fused kernel.
* **`ternary_qvm`**: Fused vector-matrix kernel (`transpose=False`).
* **`ternary_qmv`**: Fused matrix-vector general kernel (`transpose=True`, arbitrary $K$ and $N$).
* **`ternary_qmm_t`**: Tiled GEMM kernel built on real Apple `steel::BlockMMA` primitives for large-$M$ workloads — a benchmark-verified 1.25–1.7× speedup over the composed fallback.

Every `quantized_matmul` shape is now fused **except** batched weights (`w.ndim() > 2`), which still compose.

### Deferred Work
* Swift bindings (for Osaurus integration).
* Split-$K$ kernel variants.
* `qmv_wide` / `qmv_quad` kernel refinements.

*Deferred items do not affect functional correctness; every tensor shape retains a working execution path.*

## Correctness & Numerical Tolerance

Correctness is validated against a `float64` ground truth and verified by benchmark, not assumed. A documented scale-tie-breaking tolerance model accounts for a known large-$K$ discrepancy — a property of ternary scale quantization, not a kernel bug.

## Quickstart

Real, working code — `mode="ternary"` on the same `mx.quantize`/
`mx.quantized_matmul` API every other quantization mode in MLX uses:

```python
import mlx.core as mx

x = mx.random.normal((16, 4096))
w = mx.random.normal((4096, 4096))

w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
y = mx.quantized_matmul(x, w_q, scales, group_size=64, bits=2, mode="ternary")
```

## Credits

Forked from Apple's [MLX](https://github.com/ml-explore/mlx). Part of the `rivaquant` / BitNet b1.58 lineage.
