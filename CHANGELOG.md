# Changelog

MLX-QUANT is a standalone fork of [ml-explore/mlx](https://github.com/ml-explore/mlx)
maintained by [8b-is](https://github.com/8b-is). It is not intended to be
upstreamed. Versions here are independent of upstream MLX's own version
numbers (this fork branched from upstream `973e27f8`, tagged `v0.32.0` in
upstream's own scheme).

## v1.0.0

First tagged release of this fork's headline feature: a native **ternary
("BitNet b1.58") quantization mode** — 2-bit codes `{0, 1, 2}` decoding to
signed `{-1, 0, 1}` via `code - 1`, one real-valued scale per group (no
bias), 16 codes packed per `uint32` word LSB-first. Usable via the existing
`mx.quantize`/`mx.dequantize`/`mx.quantized_matmul` API with
`mode="ternary"`, `bits=2`.

### CPU backend

- Native ternary quantize/dequantize and `quantized_matmul`, wired through
  the same primitive/dispatch machinery as `"affine"` and the `"mxfp4"`/
  `"mxfp8"`/`"nvfp4"` family.
- Fused, M-tiled SIMD `quantized_matmul` kernel (`mlx/backend/cpu/
  quantized.cpp`): decodes packed weight words once per output column per
  M-tile (`MTILE=4`) and reuses them across all 4 rows' accumulators,
  instead of unpacking per row. Falls back to a correctness-first
  unpack+BLAS path for `transpose=false`, group sizes that don't divide a
  whole packed word, and `bfloat16` (no real SIMD width on this backend).
- Measured (see `benchmarks/python/ternary_qmm_bench.py`): 2.3–2.4x faster
  than this codebase's own best comparable CPU kernel (`affine`, bits=4)
  and 8–17x faster than `affine` bits=2 (no SIMD path in this codebase at
  all). Still ~14–18x slower than dense fp32 BLAS — an honest gap shared
  by every hand-rolled, non-multi-threaded CPU kernel in this codebase,
  not specific to ternary.

### GPU (Metal) backend

- Real Metal kernels for standalone `quantize`/`dequantize`
  (`mlx/backend/metal/kernels/ternary_quantized.h`), covering group sizes
  32/64/128 and `float`/`float16`/`bfloat16`, adapted from `affine_quantize`'s
  generic per-group SIMD reduction (mean-of-abs instead of min/max range,
  no bias).
- A fused `ternary_qmv_fast` kernel for the common `nn.Linear`/decode shape
  (non-batched weights, `transpose=True`, `N % 8 == 0`, `K % 1024 == 0`),
  mirroring `fp_qmv_fast_impl`'s threading model. Dispatched through a
  dedicated `fast::TernaryQmvFast` primitive rather than through
  `QuantizedMatmul`'s shared dispatch tree, so it can't leave any
  shape/dtype combination reaching a kernel name that doesn't exist.
  Measured: 2.9–6.1x faster than the compose fallback below, and 1.6–2.8x
  faster than dense fp32 GPU matmul at `M=1`.
- Every other `quantized_matmul` shape/setting (batched weights,
  `transpose=False`, or either divisibility check failing) composes
  `dequantize` + the existing dense GPU matmul instead of a fused kernel —
  correct for any shape, at the cost of not being fused. Gradients flow
  through this same fallback (`fast::Custom`'s fallback-based vjp/jvp), so
  autodiff works for the fused path too without a bespoke implementation.
- **Not implemented on GPU**: a general (non-`qmv_fast`) tiled matmul
  kernel family (`qmv`/`qmv_wide`/`qmm`/`qmm_splitk`/`qvm`/`qvm_split_k`) —
  those shapes use the compose fallback, not a fused kernel.
  `gather_qmm` (MoE-style indexed matmul) still raises for `mode="ternary"`
  on both CPU and GPU — out of scope for this release.

### Known gaps / explicitly out of scope for v1.0.0

- No Swift bindings (`mlx-swift`) — this release covers the C++/Python
  fork only. Consuming this from a Swift project (e.g. Osaurus) would
  require a separate port, not started.
- No `gather_qmm` (MoE) support for `mode="ternary"`.
- No fused GPU kernel beyond the single `qmv_fast` shape described above.

### Testing

`python/tests/test_quantized.py`: quantize/dequantize round-trip and
`quantized_matmul` correctness against an independent RoundClip reference,
covering CPU and GPU, all 3 group sizes, `float32`/`float16`/`bfloat16`,
both `transpose` settings, batched activations, and every GPU fast-path
fallback boundary (`K` not a multiple of 1024, `N` not a multiple of 8,
batched weights). Full `mlx` C++ test suite and full `python/tests` suite
pass on both a Metal-enabled and a CPU-only build.
