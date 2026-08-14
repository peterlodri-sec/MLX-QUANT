#!/usr/bin/env bash
# nightly-quantal.sh — start the nightly quantal ternary training on a vast GPU.
#
# Protocol (as of the ternary-threshold round):
#   - base model  Qwen/Qwen2.5-0.5B
#   - corpus      MLX-QUANT/data/train_ultra_qwen3.jsonl (20,007 samples)
#   - quantizer   weight_quant: true thresholded ternary (per-group 64 scale,
#                 zero state), deployed-forward BitLinear (no per-projection
#                 norm / activation_quant) — training == deployed == Rust.
#   - masked CE, dynamic pad x64, stratified val 90, early stop pat 5.
#
# Usage (on the vast box, from the MLX-QUANT checkout):
#   bash nightly-quantal.sh [--epochs N] [--batch-size N]
set -euo pipefail

EPOCHS="${EPOCHS:-40}"
BATCH="${BATCH:-12}"
MAXLEN="${MAXLEN:-256}"
CORPUS="data/train_ultra_qwen3.jsonl"
OUTDIR="ckpts-nightly"
CURVE="curve-nightly.jsonl"

# fork-mlx + mlx_lm in the system python3 (needed for the per-group ternary
# export later; training itself only needs mx + mlx_lm).
python3 -c "import mlx.core, mlx_lm" 2>/dev/null || pip3 install --quiet --break-system-packages mlx-lm

export PYTHONPATH="$PWD/python:$PWD/scripts"
echo "=== nightly quantal ternary (thresholded) run ==="
python3 scripts/train_quantal_long.py \
  --model Qwen/Qwen2.5-0.5B \
  --data "$CORPUS" \
  --batch-size "$BATCH" \
  --max-len "$MAXLEN" \
  --epochs "$EPOCHS" \
  --val-size 90 \
  --outdir "$OUTDIR" \
  --curve "$CURVE" \
  --deployed-forward
echo "FINAL_MASKED_VAL captured above; best -> $OUTDIR/quantal-long-best.safetensors"
