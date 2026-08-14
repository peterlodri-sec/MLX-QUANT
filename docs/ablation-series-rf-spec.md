# Series R/F ablation spec — the zero state's honest price

**Where:** answer to Dipankar round-6 §2 (rate-constant vs format-constant)

## Question

Does the ternary zero state earn its bits? At **2.500 bits/weight** (2-bit payload
+ f32-per-64 scale) it must buy a lot of loss. At **2.079** (entropy-coded payload)
it must buy much less — and it is the same zero state either way. The ablation
decides whether the deployed format stays ternary (2-bit codes, ~29% zeros) or
moves to sign+scale (1-bit, zero band folded into the scale).

## Protocol (same corpus, same base, same masked-CE, same val split)

Corpus: `data/train_ultra_qwen3.jsonl` (20,007 samples). Base: `Qwen/Qwen3-1.7B`
(the deployable-brain size — fast convergence, and its floor 1.9007 is measured).
Protocol: `train_quantal_long.py` — masked CE, stratified val 90, dynamic pad x64,
max-len 256, deployed-forward (weight-quant-only BitLinear), early stop pat 5,
min-delta 0.05, lr 3e-4 → 3e-5 cosine. Seed 42.

## Series R — rate-constant (~2.5 bits/weight)

Both arms ship ~2.5 bits/weight; the ONLY difference is the zero state.

- **R-ter**: ternary as shipped — 2-bit codes, per-64-group scale (the current
  `weight_quant`, threshold 0.5). Rate = 2.000 + 0.500 = 2.500 bits/weight.
- **R-sign**: sign + scale at the same rate — 1-bit codes (−1/+1, no zero state)
  with a scale grid whose entropy + 1.000 = 2.500. Concretely: per-64-group scale
  quantized to 6 bits (64 levels, entropy ≈ 1.5 max → 1.0 code + 1.5 scale = 2.5),
  or a two-scale sign with finer group structure. The rule: `q = sign(w)·scale_g`
  with `scale_g` rounded to a 6-bit grid so the rate matches 2.5.
  Implementation: `weight_quant(w, threshold=0.0)` (zero band empty) + a
  `scale_quant(scale_g, bits=6)` step applied in the forward so training sees it.

Decision metric: `ΔCE = val(R-sign) − val(R-ter)` on the same val split.
- ΔCE > +0.05 → ternary wins (zero state buys real loss at equal rate) → keep 2-bit.
- ΔCE ≈ 0 → the zero state is free at equal rate → keep it (format honest, no cost).
- ΔCE < −0.05 → sign wins → move deployed format to sign+scale.

## Series F — format-constant (reference series, not the verdict)

- **F-ter**: ternary as shipped, 2.500 bits/weight.
- **F-sign**: sign + f32-per-64 scale, 1.500 bits/weight (the natural sign format).
Reported for the record — this is the comparison the round-6 reply said would
"charge the zero state for packing", so it is NOT the decision metric.

## Controls

1. **Threshold sanity**: rerun R-ter with threshold ∈ {0.4, 0.5, 0.6} — if the
   zero fraction moves but ΔCE barely does, the third state is loss-neutral
   (supports sign+scale). If ΔCE tracks the threshold, the zero state is load-bearing.
2. **Scale-grid sanity**: R-sign with 5-bit vs 6-bit scale grid — confirms the
   rate accounting is not the confound.
3. **Same-corpus head-to-head**: this run's numbers vs the published 2.1469
   (different corpus — not comparable; the point of this ablation is the SAME
   corpus under both rules, which is why it supersedes the 2.1469-vs-1.6998 read).

## Expected run budget (1.7B, ~2s/step measured on H100)

- 2 arms × 3 epochs ≈ 2 × 90 min ≈ 3h (early-stop likely sooner on 20k corpus).
- Threshold sweep adds ~1h. Total ≈ 4h on an H100; ~8-10h on a 24GB A6000-class
  with the int8-Adam/bf16-grads recipe.

## Outputs

- `curve-r-ter.jsonl`, `curve-r-sign.jsonl`, `curve-f-sign.jsonl` + best checkpoints.
- A table: arm | rate (bits/weight) | val masked-CE | zero fraction.
- The verdict line: `ZERO_STATE_DECISION=keep|drop` with the ΔCE that drove it.

## Dependencies

- Needs `weight_quant` to accept `threshold=0.0` (already does — the `where` with
  an empty zero band) and a small `scale_quant` addition for R-sign's grid.
- Runs on the same box env as the nightly (`mlx 0.30.0` + `mlx-cuda 0.30`,
  PYTHONPATH fork overlay, H100/Ampere/Ada only — NOT Turing/Blackwell).
