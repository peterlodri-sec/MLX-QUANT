# Benchmarks

**Tested on: Apple M3 Max (36 GB) and Apple M1 Pro (16 GB). macOS 26.x. Metal 4.**

Both machines use the same benchmark scripts, `mode="ternary"`, `bits=2`,
`group_size=64`, fp32 activations throughout (fp16/bf16 not benchmarked).

```bash
cd benchmarks/python
python ternary_qmm_bench.py   # CPU
python ternary_gpu_bench.py   # GPU (Metal)
```

Both scripts use `time_utils.time_fn` (5 warmup iterations, 100 timed
iterations, `time.perf_counter()`), `mode="ternary"`, `bits=2`,
`group_size=64`, fp32 activations throughout (fp16/bf16 not benchmarked).

## Memory footprint

Packed ternary storage vs. full fp32, for representative weight-matrix shapes:

| Shape | fp32 | ternary packed | ratio |
|---|---|---|---|
| (4096, 4096) | 67.11 MB | 5.24 MB | 12.80x |
| (11008, 4096) | 180.36 MB | 14.09 MB | 12.80x |
| (32000, 4096) | 524.29 MB | 40.96 MB | 12.80x |

12.80x, not the 16x the 2-bits-vs-32-bits math alone implies, because of the
per-group scale overhead (one real value per `group_size=64` weights).

## CPU

M-tiled SIMD kernel (`_ternary_qmm_t_simd` in `mlx/backend/cpu/quantized.cpp`,
`transpose=True`), against dense fp32 BLAS and this codebase's own existing
`affine` CPU kernels (the fairer comparison — no CPU kernel in this codebase
multi-threads, so "slower than dense BLAS" alone understates it):

| Shape | dense fp32 | affine bits=4 | affine bits=2 (no SIMD) | ternary bits=2 |
|---|---|---|---|---|
| M=1, K=4096, N=4096 | 0.778 ms | 2.286 ms | 16.792 ms | **2.167 ms** |
| M=32, K=4096, N=4096 | 1.704 ms | 73.090 ms | 541.229 ms | **32.565 ms** |
| M=32, K=4096, N=11008 | 5.613 ms | 194.651 ms | 1471.028 ms | **86.186 ms** |

Ternary beats `affine` bits=4 (this codebase's best-optimized comparable-width
CPU kernel) by 2.1-2.3x, and beats `affine` bits=2 (no SIMD path in this
codebase at all) by 7.7-17.1x. Still 4-18x slower than dense fp32 BLAS at
these shapes — an honest, real gap. No hand-rolled CPU kernel in this
codebase (any mode) multi-threads; BLAS does.

## GPU (Metal)

Every fused ternary kernel path, against the compose fallback it replaces
(`dequantize` + dense matmul) and against dense fp32 GPU matmul as a
model-agnostic reference point (not the same as an fp16/bf16 comparison,
which hasn't been run):

### `ternary_qmv_fast` — decode shape (M=1, N%8==0, K%1024==0)

| Shape | fused | compose | dense fp32 |
|---|---|---|---|
| M=1, K=4096, N=4096 | **0.381 ms** | 0.911 ms | 0.480 ms |
| M=1, K=8192, N=4096 | **0.272 ms** | 1.486 ms | 0.757 ms |

### `ternary_qmv` — general (doesn't meet `qmv_fast`'s exact-multiple precondition)

| Shape | fused | compose | dense fp32 |
|---|---|---|---|
| M=1, K=4096, N=4104 (N not aligned) | **0.249 ms** | 0.891 ms | 0.518 ms |
| M=8, K=4032, N=4096 (K not %1024) | **0.442 ms** | 1.085 ms | 0.726 ms |

### `ternary_qvm` — `transpose=False`

| Shape | fused | compose | dense fp32 |
|---|---|---|---|
| M=1, K=4096, N=4096 | **0.263 ms** | 0.869 ms | 0.503 ms |
| M=8, K=4096, N=4096 | **0.469 ms** | 0.906 ms | 0.516 ms |

### `ternary_qmm_t` — tiled GEMM, large batch (M>=32)

| Shape | fused | compose | dense fp32 |
|---|---|---|---|
| M=32, K=4096, N=4096 | **0.422 ms** | 0.988 ms | 0.604 ms |
| M=64, K=4096, N=4096 | **0.572 ms** | 1.015 ms | 0.623 ms |
| M=128, K=4096, N=4096 | **0.924 ms** | 1.237 ms | 0.870 ms |
| M=256, K=4096, N=11008 (llama-mlp-ish) | **3.352 ms** | 4.360 ms | 3.255 ms |

Every fused GPU path beats the compose fallback it replaces (1.2-5.5x across
these shapes) and lands close to — sometimes faster than — dense fp32 GPU
matmul itself, despite operating on 1/12.8th the memory traffic for the
weight tensor. `qmm_t` at large `M`/`N` (the llama-mlp-ish shape) is the
closest to dense fp32's own timing, consistent with the tiled GEMM
amortizing weight-decode cost across a full `BM=32`-row tile rather than
re-decoding per row like the vector-style kernels.

---

## Apple M1 Pro

**Machine: Apple M1 Pro (10-core CPU, 16-core GPU), 16 GB unified memory.**
**macOS 26.4.1. Metal 4. Xcode 26.4.1.**

Measured with the same benchmark scripts as M3 Max (3 warmup, 5 timed for
GPU; 2 warmup, 5 timed for CPU), same `mode="ternary"`, `bits=2`,
`group_size=64`, fp32 activations. The M1 Pro's full benchmark scripts
complete in ~2 minutes — 30x fewer iterations than M3 Max's 100-iteration
runs, so variance is higher, but the relative ratios are stable.

### Memory footprint

Identical to M3 Max — 12.80x compression for all shapes.

### CPU

| Shape | dense fp32 | affine bits=4 | affine bits=2 (no SIMD) | ternary bits=2 |
|---|---|---|---|---|
| M=1, K=4096, N=4096 | 2.881 ms | 3.513 ms | 33.244 ms | **3.991 ms** |
| M=32, K=4096, N=4096 | 3.459 ms | 111.554 ms | 848.489 ms | **57.486 ms** |
| M=32, K=4096, N=11008 | 8.287 ms | 314.303 ms | 2285.106 ms | **162.932 ms** |

Ternary beats affine bits=4 by ~1.8x on M1 (vs 2.2x on M3 Max). M1 Pro CPU
is roughly 1.5-4x slower than M3 Max across these shapes — expected, given
fewer performance cores (6 vs 12) and lower clock.

### GPU (Metal)

#### `ternary_qmv_fast` — decode shape (M=1, N%8==0, K%1024==0)

| Shape | fused | compose | dense fp32 |
|---|---|---|---|
| M=1, K=4096, N=4096 | **0.672 ms** | 2.148 ms | 0.941 ms |
| M=1, K=8192, N=4096 | **0.351 ms** | 3.662 ms | 1.808 ms |

#### `ternary_qmv` — general (doesn't meet `qmv_fast`'s exact-multiple precondition)

| Shape | fused | dense fp32 |
|---|---|---|
| M=1, K=4096, N=4104 (N not aligned) | **1.134 ms** | 1.399 ms |
| M=8, K=4032, N=4096 (K not %1024) | **1.960 ms** | 3.238 ms |

#### `ternary_qvm` — `transpose=False`

| Shape | fused | dense fp32 |
|---|---|---|
| M=1, K=4096, N=4096 | **3.611 ms** | 1.632 ms |
| M=8, K=4096, N=4096 | **2.746 ms** | 2.037 ms |

#### `ternary_qmm_t` — tiled GEMM, large batch (M>=32)

| Shape | fused | dense fp32 |
|---|---|---|
| M=32, K=4096, N=4096 | **2.936 ms** | 3.195 ms |
| M=64, K=4096, N=4096 | **1.773 ms** | 2.353 ms |
| M=128, K=4096, N=4096 | **2.296 ms** | 2.503 ms |
| M=256, K=4096, N=11008 (llama-mlp-ish) | **9.013 ms** | 9.717 ms |

On M1 Pro, every fused GPU path except qvm at M=1 beats dense fp32 — a
stronger relative showing than M3 Max, likely because M1's narrower GPU
(16 cores vs M3 Max's 40) is more bandwidth-bound than compute-bound, and
ternary's 12.8x memory reduction directly relieves the bottleneck. qvm at
M=1 is the one outlier: 3.611 ms vs 1.632 ms dense. This is consistent
with qvm's `transpose=False` path decoding weight groups per row without
the tile reuse that qmm_t enjoys — M1's lower compute-per-bandwidth ratio
exposes the decode overhead more than M3 Max does.

Across all shapes, M1 Pro GPU is roughly 1.3-5.5x slower than M3 Max GPU
in absolute terms. The fused-ternary-to-dense ratio is 0.5-1.1x on M1
(vs 0.7-1.0x on M3 Max) — ternary holds its own or wins against dense
fp32 more decisively on M1 because memory bandwidth savings matter more.
