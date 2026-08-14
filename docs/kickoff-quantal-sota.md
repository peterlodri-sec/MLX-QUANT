# Kickoff — quantal SOTA training pipeline

You are operating the **quantal ternary SOTA pipeline** (the constellation's
BitNet b1.58 continued-train on Qwen2.5-0.5B). Your job, in order:

## 1. Check the nightly status first
- SSH to the vast instance and check the training:
  `pgrep -f train_quantal_long && tail -5 /tmp/bleeding.log`
- Read `curve-bleeding.jsonl` — the best masked val so far. The current
  published best is **2.1469** (lr 3e-4, overfits after epoch 2); the
  bleeding-edge run uses lr 5e-5 → 5e-6, patience 3.
- The nightly protocol: `scripts/nightly-quantal.sh` (40 epochs, B12/256,
  `MLX_CUDA_GRAPH_CACHE_SIZE=2000`). If the bleeding-edge run is done, export
  the best and run the parity gate before publishing.

## 2. Export the best checkpoint
On the Mac (the export is fork-free — `ternary_quantize_numpy`):
```bash
cd MLX-QUANT
PYTHONPATH="$PWD/python:$PWD/scripts" python3 scripts/export_quantal_checkpoint.py \
  --checkpoint <best.safetensors> --out-dir <demo> --model Qwen/Qwen2.5-0.5B
PYTHONPATH="$PWD/python:$PWD/scripts" python3 scripts/export_quantal_assets.py \
  --checkpoint <best.safetensors> --out-dir <demo>
```
Verify the ternary properties: zero fraction ~30%, scales are NOT a scalar
(real per-group variety), no code-3 in the packed words.

## 3. Parity gate (must PASS before publish)
```bash
# golden reference (MLX, vanilla)
uv run --python 3.11 --with mlx --with mlx-lm --with transformers --with tokenizers --with numpy \
  python3 scripts/quantal_golden_logits.py --model-dir <demo> --vanilla-only --out <demo>/ref.json
# Rust runner
cargo run -q -p ternary --example quantal_logits -- <demo> <demo>/rust.json
python3 scripts/quantal_compare_logits.py <demo>/rust.json <demo>/ref.json
```
Acceptance: max_abs ≤ 1e-2 (the best run hit 1.3e-5). Argmax must match.

## 4. Publish to HF — manifest-last ordering
Push in separate commits, in this exact order (the manifest window closes
last — Dipankar's fix):
1. `m000..m167.json` (168 matrices)
2. `embeddings.f16`, `norms.f32`, `tokenizer.json`
3. `README.md` (card — update masked val, sha, trajectory)
4. `index.json` with `export_complete: true` **last**

The `checkpoint_sha256` in the card and in `index.json` MUST match the blob.
Use `huggingface_hub` `CommitOperationAdd` per group.

## 5. Transformers parity (optional)
`scripts/quantal_to_bitnet.py --model-dir <demo> --ref <demo>/ref.json` — the
PyTorch port. Needs the transformers dev branch (`use_sub_norms` support,
PR #47955); PyPI 5.15 ignores the flag.

## Non-obvious rules
- `MLX_CUDA_GRAPH_CACHE_SIZE=2000` or mlx-cuda crashes (cudaGraph).
- The vast mlx-cuda needs `nvidia-cudnn-cu12==9.*`; a torch install that pulls
  cudnn-8 breaks it.
- safetensors `data_offsets` are relative to the data-section start
  (8 + header_len + offset). BF16 reads via bit-shift, not `mx.load`.
- Never commit `.safetensors` (gitignored) or HF credentials.
- `git add` only the intended files; verify before commit.
