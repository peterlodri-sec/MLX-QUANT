---
name: quantal-sota-training
description: Run the quantal ternary SOTA training pipeline end-to-end — thresholded-ternary deployed-forward QAT, nightly GPU run, ayeOS export, Rust parity gate, HF publish. Use when the task is "train the next quantal best", "run a nightly", "export a checkpoint", or "verify/publish a quantal run".
---

# Quantal SOTA Training Pipeline

Continued-train Qwen2.5-0.5B with a **true thresholded ternary** quantizer
(per-group 64 scale, real zero state), deployed-forward QAT (training ≡
deployed ≡ Rust), then export to the ayeOS format, parity-check against the
Rust runner, and publish to HF.

## When to invoke

Use this skill when you need to:
- Run the next nightly SOTA training (GPU, `train_ultra_qwen3.jsonl`)
- Change / verify the ternary quantizer (`weight_quant`)
- Export a checkpoint to the ayeOS 168-matrix format
- Run the Rust parity gate (MLX-vanilla vs Rust runner)
- Publish a run to `PeetPedro/quantal-ternary` on HF
- Port the deployed forward to transformers (PyTorch)

## Protocol (the non-obvious parts)

### Quantizer
`python/mlx/nn/layers/bitlinear.py` — `weight_quant` is a **thresholded
ternary**: per 64-column group, `scale = mean(|w|)`, zero when
`|w| < 0.5·scale`, else `±scale`. NOT the sign-based collapse (that had no
zero state). ~30% of weights are zero. `deployed_forward=True` is the
default — no per-projection RMSNorm, no activation_quant.

### Training (vast GPU)
```bash
export PYTHONPATH="$PWD/python:$PWD/scripts"
export MLX_CUDA_GRAPH_CACHE_SIZE=2000   # REQUIRED — default 400 crashes mlx-cuda
python3.11 scripts/train_quantal_long.py \
  --model Qwen/Qwen2.5-0.5B --data data/train_ultra_qwen3.jsonl \
  --batch-size 12 --max-len 256 --epochs 40 --val-size 90 \
  --outdir ckpts-nightly --curve curve-nightly.jsonl --deployed-forward \
  [--lr-init 5e-5 --lr-end 5e-6 --patience 3 --min-delta 0.01]  # bleeding-edge
```
- **mlx-cuda gotchas**: needs the base `mlx` + `mlx-cuda` 0.30 wheels on the
  same Python 3.11; the cudnn-9 wheel must be present (`nvidia-cudnn-cu12==9.*`)
  — a torch install that pulls cudnn-8 breaks the mlx-cuda import. Nightly best
  so far: 2.1469 (lr 3e-4, overfits after epoch 2); bleeding-edge uses lr 5e-5.
- Python deps via the system python3.11 (vast CUDA image).

### Export (Mac, fork-mlx or numpy)
The export is **fork-free** now — `ternary_quantize_numpy` packs the ayeOS
codes/scales (per-group scale from the full-precision weight):
```bash
PYTHONPATH="$PWD/python:$PWD/scripts" python3 scripts/export_quantal_checkpoint.py \
  --checkpoint <ckpt.safetensors> --out-dir <demo> --model Qwen/Qwen2.5-0.5B
PYTHONPATH="$PWD/python:$PWD/scripts" python3 scripts/export_quantal_assets.py \
  --checkpoint <ckpt.safetensors> --out-dir <demo>
```
- `data_offsets` in safetensors are **relative to the data section start**
  (8 + header_len + offset), NOT the file start. Readers must add the offset.
- BF16 tensors: read via bit-shift (`(bits << 16).view(f32)`), never `mx.load`
  on the local mlx fork (mis-reads BF16).

### Parity gate (Rust vs MLX-vanilla)
```bash
# MLX reference
uv run --python 3.11 --with mlx --with mlx-lm --with transformers --with tokenizers --with numpy \
  python3 scripts/quantal_golden_logits.py --model-dir <demo> --vanilla-only --out <demo>/ref.json
# Rust runner (entheai, or the vast build)
cargo run -q -p ternary --example quantal_logits -- <demo> <demo>/rust.json
python3 scripts/quantal_compare_logits.py <demo>/rust.json <demo>/ref.json
```
Accept: max_abs ≤ 1e-2 (best runs: 1.3e-5). Argmax must match (71703 on the
current best). If gains.f32 is present (faithful forward), the compare picks
the bitlinear reference automatically.

### HF publish — manifest-last ordering
Push in this order (Dipankar's fix — the manifest window must close last):
1. `m000..m167.json` (168 matrices)
2. `embeddings.f16`, `norms.f32`, `tokenizer.json`
3. `README.md` (card)
4. `index.json` with `export_complete: true` **last**

Use `huggingface_hub` `CommitOperationAdd` in separate commits per group.
The blob, card, and index.json must agree on `checkpoint_sha256`.

### Transformers port
`quantal_to_bitnet.py` loads the ayeOS export into `BitNetForCausalLM`
(use_sub_norms=False, rope_theta 1e6, attn_implementation="eager"). The
PyPI 5.15 `BitNetMLP`/`BitNetAttention` do NOT honour use_sub_norms — use
the dev branch (PR #47955). Parity: 6.5e-06.

## Repository map

| Path | Purpose |
|------|---------|
| `python/mlx/nn/layers/bitlinear.py` | thresholded ternary + deployed-forward |
| `scripts/train_quantal_long.py` | training (masked CE, early stop, val 90) |
| `scripts/train_quantal.py` | model surgery + ayeOS export helpers |
| `scripts/export_quantal_checkpoint.py` | 168-matrix export (numpy ternary) |
| `scripts/export_quantal_assets.py` | embeddings.f16 + norms.f32 + gains/biases |
| `scripts/quantal_golden_logits.py` | MLX reference forward (vanilla + bitlinear) |
| `scripts/quantal_compare_logits.py` | parity gate |
| `scripts/quantal_to_bitnet.py` | transformers loader + PyTorch parity |
| `scripts/nightly-quantal.sh` | GPU nightly runner |
| `data/train_ultra_qwen3.jsonl` | 20,007-sample corpus |
| `ckpts-nightly/` | best + final checkpoints (gitignored) |

## Constraints

- `nix-base` conventions: formatter `nixpkgs-fmt` for Nix; Python via `uv`
  (except the fork-mlx export path, which needs system python3).
- Never commit `.safetensors` (gitignored) or HF credentials.
- The current published best: `21294c68…8285`, masked val 2.1469, parity 1.3e-5.
