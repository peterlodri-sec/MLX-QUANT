# Teacher–student distillation spec — quantal ternary brain from Qwen3-32B-FP8

## Verdict from verification

- **Teacher: `Qwen/Qwen3-32B-FP8`** (Apache 2.0, dense, fp8 e4m3 block-128, ~16GB
  weights). Tokenizer **byte-identical to the student** (Qwen3, vocab 151,643,
  0 missing, all IDs match) → **logits-level KL distillation is valid**.
- **NOT `Qwen3.8-27B-FP8`**: that teacher is Qwen3.5 — tokenizer vocab 248,044,
  shifted IDs (`Ġp` 281→280, …), 20,057 student tokens missing. Per-position
  logits alignment is impossible; the only play there is sequence-level
  (data-generation), which we keep as a secondary lane.
- **Student: the quantal ternary brain** (Qwen3-1.7B base → thresholded ternary,
  deployed-forward, ayeOS export, Rust runner). Target size for this lane.

## Why logits-KL (not just text)

Masked-CE teaches the student the *text*. KL against the teacher's softmax teaches
the *decision distribution* — the 32B's confidence structure, its near-misses,
its abstention pattern. For a tiny ternary model this is the classic
small-beats-its-size play: the student inherits not only what the teacher would
say but how much it believes it. The zero-state cost question (Series R/F) is
also sharper under teacher logits than under raw masked-CE.

## Protocol

### Phase 1 — teacher logits (one-time, on the 80GB box)

`scripts/teacher_logits.py` (new):
- Load `Qwen/Qwen3-32B-FP8` via the 8b-is transformers fork (fp8 quantizer;
  fall back to the HF transformers if the fork lacks fp8 support — verify).
- Tokenize the corpus (`data/train_ultra_qwen3.jsonl`) with the Qwen3 tokenizer
  (byte-identical to student — same ids, so NO re-tokenization seam).
- For each sample: `logits = teacher(input_ids)`; take the **top-64 logits per
  position** (enough for KL, 1/2365 of full-vocab storage) → store
  `{token_id: logit}` sparse per position.
- Output: `data/teacher_logits/` — one `.npz` per sample:
  `{ids: uint32[n], top_ids: uint32[n,64], top_logits: f32[n,64], mask: bool[n]}`.
  Batch 8, max-len 256, fp8, MLX_CUDA_GRAPH_CACHE_SIZE=2000 env.
- Cache in a bucket/object store per the hf-mac rule (NOT the M1).

### Phase 2 — student training with KL

`scripts/train_quantal_distill.py` (new, or a `--distill` flag in
`train_quantal_long.py`):
- Loss = `λ·masked_CE + (1−λ)·masked_KL`, λ annealed 1.0 → 0.5 over the run.
- `masked_KL`: for each position, gather the student logits at the teacher's
  top-64 ids, softmax both, sum `p_teacher·log(p_teacher/p_student)` (KL), masked
  over valid tokens (pad token 0 weighted out — same mask as CE).
- Student forward stays the **deployed-forward thresholded ternary BitLinear**
  (parity invariant untouched: the Rust runner reads codes+scales, and the
  teacher-KL only changes the loss, not the forward).
- Same stratified val 90, early stop pat 5 / min-delta 0.05, lr 3e-4 → 3e-5.
- Compare against the masked-CE-only baseline on the SAME val split (the
  distillation win = `val_distill < val_ce_only`).

### Phase 3 — export + parity + publish (unchanged pipeline)

Best checkpoint → `export_quantal_checkpoint.py` + `export_quantal_assets.py` →
parity gate (Rust vs MLX, ≤1e-2) → HF manifest-last publish.

## Budget (H100, 1.7B student)

- Phase 1: 20k samples × ~200 tok/sample through 32B fp8 ≈ 4M tok @ ~150 tok/s
  ≈ ~8h (one-time; can subsample to 10k for a probe run first).
- Phase 2: 1.7B student, ~2s/step × 2489 steps/epoch ≈ 1.4h/epoch; 5–10 epochs
  ≈ 7–14h.
- Total ≈ one 24h window on the box.

## Secondary lane (kept)

`Qwen3.8-27B-FP8` as **data generator / judge** (sequence-level, tokenizer-
agnostic): teacher writes continuations/rewrites for corpus prompts → corpus
expansion 20k → 60–100k, plus preference pairs for a future DPO round. This is
the "szedjünk datasetet" TODO and the 27B's real role. Runs on the same box,
interleaved with Phase 1.

## Open decisions for the operator

1. Phase-1 subsample: probe on 10k samples (~4h) before the full 20k?
2. λ schedule: fixed 0.5 vs annealed 1.0→0.5 (anneal recommended).
3. Top-k for KL: 64 (recommended) vs 128.
4. Box: the H100 that's queued for restart, or a fresh one.
