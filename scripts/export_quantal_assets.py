#!/usr/bin/env python3
"""
export_quantal_assets.py — emit the non-ternary model pieces (token embedding
matrix + RMSNorm gain vectors) for the quantal ayeOS export so the ternary
BitNet model becomes runnable end-to-end in Rust.

Background
----------
export_quantal_checkpoint.py emits the 168 per-layer ternary matrix files
(mNNN.json) that carry the quantized BitLinear weights (packed codes +
per-group scales). Those alone cannot generate text — the runtime also needs:

  (a) the token embedding matrix ``model.embed_tokens.weight``
      [151936, 896] (vocab x hidden). This MUST come from the trained
      checkpoint: quantal is a continued-trained model, so the stock Qwen
      embeddings are a different model's tensors.
  (b) the 49 RMSNorm gain vectors (24 layers x {input, post_attention}
      + final norm).

This script reads the checkpoint safetensors directly (``mlx.load``) and
writes two raw binary assets next to the mNNN.json files:

  embeddings.f16 — BF16 -> FP16, raw little-endian bytes, shape [151936, 896]
                   size 151936*896*2 = 272,269,312 bytes (~272.3 MB)
  norms.f32      — BF16 -> FP32, raw little-endian bytes, shape [49, 896]
                   size 49*896*4 = 175,616 bytes (~171.5 KB)

The checkpoint stores these tensors in BF16; the conversion to FP16/FP32 is a
numeric dtype cast via mlx (``astype``), NOT a raw bit copy — interpreting raw
BF16 bits as FP16 would give garbage values.

Both asset files are gitignored (embeddings.f16 exceeds GitHub's 100 MB
per-file limit); only their sha256 metadata is committed in index.json.

norms.f32 row ordering (exact; document this in the Rust loader)
----------------------------------------------------------------
    row 2*i   : model.layers[i].input_layernorm.weight         (i = 0..23)
    row 2*i+1 : model.layers[i].post_attention_layernorm.weight (i = 0..23)
    row 48    : model.norm.weight  (final RMSNorm)

i.e. layer 0 input, layer 0 post_attention, layer 1 input, layer 1
post_attention, ..., layer 23 input, layer 23 post_attention, final norm.
49 rows total, 896 fp32 floats per row (hidden_size).

Usage:
  python scripts/export_quantal_assets.py \
    --checkpoint demos/quantal/quantal_model.safetensors \
    --out-dir demos/quantal
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import cast

import mlx.core as mx
import numpy as np

VOCAB_SIZE = 151936
HIDDEN_SIZE = 896
N_LAYERS = 24
EXPECTED_NORMS = 2 * N_LAYERS + 1  # 49

EMBED_KEY = "model.embed_tokens.weight"
FINAL_NORM_KEY = "model.norm.weight"
LAYER_NORM_KEYS = (
    "input_layernorm.weight",
    "post_attention_layernorm.weight",
)

EMBED_FNAME = "embeddings.f16"
NORMS_FNAME = "norms.f32"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", required=True, help="trained quantal safetensors")
    p.add_argument("--out-dir", required=True, help="pocoo demo dir (m*.json + index.json live here)")
    args = p.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    idx_path = out / "index.json"
    if not idx_path.exists():
        sys.exit(f"error: {idx_path} not found — run export_quantal_checkpoint.py first")

    print(f"  mlx: {getattr(mx, '__version__', 'unknown')}")
    print(f"  metal: {mx.metal.is_available()}")

    print("1. loading checkpoint...")
    w = cast(dict, mx.load(args.checkpoint))
    if EMBED_KEY not in w:
        sys.exit(f"error: '{EMBED_KEY}' not found in checkpoint")
    if FINAL_NORM_KEY not in w:
        sys.exit(f"error: '{FINAL_NORM_KEY}' not found in checkpoint")

    # --- (a) token embeddings -------------------------------------------------
    print("2. exporting embeddings.f16 ...")
    emb = w[EMBED_KEY]
    assert tuple(emb.shape) == (VOCAB_SIZE, HIDDEN_SIZE), (
        f"unexpected embed shape {emb.shape}"
    )
    print(f"   {EMBED_KEY}: shape={emb.shape} dtype={emb.dtype}")
    emb_f16 = emb.astype(mx.float16)
    emb_bytes = np.asarray(emb_f16, dtype="<f2").tobytes()
    emb_path = out / EMBED_FNAME
    emb_path.write_bytes(emb_bytes)
    emb_size = emb_path.stat().st_size
    print(f"   wrote {emb_path} ({emb_size:,} bytes, shape [151936, 896])")

    # --- (b) RMSNorm vectors --------------------------------------------------
    print("3. exporting norms.f32 ...")
    rows = []
    for i in range(N_LAYERS):
        for suffix in LAYER_NORM_KEYS:
            key = f"model.layers.{i}.{suffix}"
            if key not in w:
                sys.exit(f"error: '{key}' not found in checkpoint")
            rows.append(w[key])
    rows.append(w[FINAL_NORM_KEY])
    assert len(rows) == EXPECTED_NORMS

    norms = mx.stack([r.astype(mx.float32) for r in rows])  # [49, 896]
    assert tuple(norms.shape) == (EXPECTED_NORMS, HIDDEN_SIZE), norms.shape
    norms_bytes = np.asarray(norms, dtype="<f4").tobytes()
    norms_path = out / NORMS_FNAME
    norms_path.write_bytes(norms_bytes)
    norms_size = norms_path.stat().st_size
    print(f"   wrote {norms_path} ({norms_size:,} bytes, shape [49, 896])")
    print("   ordering: for i in 0..23: input_layernorm(i), post_attention_layernorm(i); then final model.norm.weight")

    # --- hashes + index.json --------------------------------------------------
    print("4. hashing assets...")
    emb_sha = sha256_of(emb_path)
    norms_sha = sha256_of(norms_path)
    print(f"   {EMBED_FNAME} sha256 {emb_sha}")
    print(f"   {NORMS_FNAME} sha256 {norms_sha}")

    print("5. updating index.json (assets section)...")
    with open(idx_path, "r") as f:
        index = json.load(f)
    index["assets"] = {
        EMBED_FNAME: {
            "dtype": "f16",
            "shape": [VOCAB_SIZE, HIDDEN_SIZE],
            "bytes": emb_size,
            "sha256": emb_sha,
            "source": "quantal_model.safetensors model.embed_tokens.weight (BF16->FP16)",
        },
        NORMS_FNAME: {
            "dtype": "f32",
            "shape": [EXPECTED_NORMS, HIDDEN_SIZE],
            "bytes": norms_size,
            "sha256": norms_sha,
            "source": "quantal_model.safetensors RMSNorm weights (BF16->FP32)",
        },
    }
    # json.dump-style (no trailing newline), matching export_quantal_checkpoint.py
    with open(idx_path, "w") as f:
        json.dump(index, f, indent=2)
    print(f"   updated {idx_path}")

    print("  done")


if __name__ == "__main__":
    main()
