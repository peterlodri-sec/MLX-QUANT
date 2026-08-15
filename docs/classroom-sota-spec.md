# CLASSROOM-SOTA training spec — ring-of-teachers distillation for the quantal brain

**Goal:** beat the single-teacher distillation baseline (Qwen3-8B → 1.7B ternary
student, KL+CE) with a **ring of teachers** whose consensus the student learns.
The classroom is deliberately MIXED: a logits-KL "teaching faculty" (tokenizer-
matched teachers) + a sequence-level "seminar" (tokenizer-mismatched teachers
generating corpus text). This is the classic ensemble-distillation win: the
student binds to the ring's consensus, not any single teacher's errors.

## Verified ring roster (tokenizer checks done 2026-08-15)

### Faculty — logits-KL capable (tokenizer byte-identical to the Qwen3 student)

| teacher | size | specialty | vocab | logits-KL |
|---|---|---|---|---|
| `Qwen/Qwen3-8B` (current baseline) | 8B | general | 151,643 ✓ | ✓ |
| `PeetPedro/Qwen3-30B-A3B-ToolCaller` | 30B/3B-act | agentic/tool-use | 151,643 ✓ | ✓ |
| (optional) a Qwen3-14B/32B | 14-32B | general | 151,643 ✓ | ✓ |

Faculty loss target: **`mean(logits)` over the ring** — geometric-mean softmax
(equivalent to averaging log-probs), NOT one teacher's logits. This is the
consensus the student learns.

### Seminar — sequence-level only (tokenizer mismatch, generate text)

| teacher | size | specialty | vocab | role |
|---|---|---|---|---|
| `PeetPedro/gpt-oss-120b-heretic` | 120B | reasoning | 199,998 ✗ | corpus generator |
| `PeetPedro/qwen2.5-coder-32b-heretic` | 32B | code | (gated) ✗ | corpus generator |
| `PeetPedro/kompress-v17/v33` | small | compression | 50,280 ✗ | corpus generator |

Seminar role: expand the corpus (20k → 60-100k) with teacher-generated
domain text that flows into the masked-CE term. Tokenizer-agnostic by design.

### Excluded (verified no tokenizer.json / config-only)

`anonymus-1bit-gpt`, `rivaquant`, `axiom-quant-demo`, `unit`, `ultrawhale-dogfood`.

## Loss

```
loss = α·masked_CE(corpus + seminar-generated) + β·KL(student ∥ mean(faculty_logits))
```

- α, β: annealed — start β=0 (CE-only warmup, a few epochs to stabilize the
  quantizer), then ramp β to 0.5. The faculty term only makes sense once the
  student's CE is in a sane regime.
- masked_CE unchanged (pad token 0 weighted out).
- KL as in `train_quantal_distill.py` (top-k sparse, sha1-aligned cache lookup).
- **Student forward is the deployed-forward thresholded ternary BitLinear —
  unchanged.** The parity invariant (training == Rust runner) is untouched: the
  Rust runner reads codes+scales, the faculty-KL and seminar-CE only change the
  loss.

## Pipeline (extends the current distillation lane)

### Phase 1 — faculty logits caches (per teacher, on the box)

`teacher_logits.py --teacher <T> --out data/classroom/<T-slug>/` for each faculty
member. Cache format identical (sparse top-k per sample, sha1-named npz,
manifest with teacher id + top_k + tokenizer id).

- Qwen3-8B: ~14 sample/s (measured) → 20k ≈ 25 min
- A3B-ToolCaller (30B): ~2× slower → 20k ≈ 50 min
- Budget: ~1.5h total for the faculty on the H100.

### Phase 1b — seminar corpus generation (sequence-level)

For each seminar teacher: prompt the 20k corpus samples, generate continuations/
rewrites (max_new_tokens ~128), append to `data/train_classroom.jsonl`. Tokenizer
mismatch is irrelevant — we keep only the TEXT. Quality-gate: keep generations
whose teacher-logprob per token is above a threshold (reject degenerate loops).

- gpt-oss-120b-heretic is heavy (120B); run it only on a 10k subsample or use the
  coder/kompress teachers for bulk and gpt-oss for a curated 2-3k.
- Budget: ~1-2h interleaved with faculty cache generation.

### Phase 2 — student training

`train_quantal_classroom.py` (new; extends `train_quantal_distill.py`):

- `--faculty-dirs data/classroom/qwen3-8b data/classroom/a3b-toolcaller`
- `--seminar-data data/train_classroom.jsonl`
- `--faculty-weight 0.5 --ce-weight 0.5`
- Per-sample: load each faculty's top-k cache for the sample hash, gather the
  student logits at the union of top-k ids across faculty, softmax each faculty
  distribution, average log-probs → KL target. Missing cache → that faculty
  contributes 0 for that sample (never crash).
- Seminar text flows through `load_jsonl` → masked-CE as usual.
- Same stratified val 90, early stop pat 5 / min-delta 0.05, lr 3e-4 → 3e-5.
- Curve jsonl adds `faculty_kl`, `seminar_ce`, `faculty_weight` per epoch.

## Baseline to beat

The single-teacher distillation run in flight (Qwen3-8B → 1.7B, KL 0.5 + CE)
and the CE-only baseline (2.1469 line). The classroom wins if
`val_classroom < val_single_teacher` on the SAME val split. A/B on the same
corpus, same seed.

## Verification gates

1. Faculty cache manifests: each `manifest.json` reports tokenizer_id 151643 and
   top_k matching the student's — mismatch = hard error (cache is useless).
2. Seminar corpus: distinct-sample count, no degenerate generations
   (quality gate above), sample count logged.
3. Parity: after export, the Rust-vs-MLX gate must still pass ≤1e-2 (the forward
   never changed — the loss did).
4. Zero-state (Dipankar): re-run the zero-fraction probe on the classroom best
   checkpoint — the faculty consensus may shift the zero appetite vs the
   single-teacher run.

## Budget (H100, 1.7B student)

- Phase 1 (faculty): ~1.5h
- Phase 1b (seminar): ~1-2h (interleaved)
- Phase 2: ~7-14h (5-10 epochs)
- Total: ~10-18h on one H100 window.

## Open decisions

1. Faculty size: 2 (8B + A3B) or 3 (add 14B/32B)? Start with 2 — the marginal
   value of a 3rd Qwen3-tokenizer teacher is small vs the cache cost.
2. Faculty averaging: geometric-mean softmax (recommended) vs weighted (by
   teacher reliability — not measurable yet, so equal weights first).
3. Seminar bulk: coder-32b + kompress for volume, gpt-oss-120b curated 2-3k.
4. β ramp: start β=0 for N epochs, then ramp — N=2 recommended (quantizer needs
   CE to stabilize first).
