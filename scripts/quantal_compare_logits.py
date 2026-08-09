#!/usr/bin/env python3
"""
quantal_compare_logits.py — GOLDEN-LOGITS GATE.

Compares the Rust runner's final-token logits
(`cargo run -p ternary --example quantal_logits -- <model_dir> <rust.json>`)
against the MLX reference (`quantal_golden_logits.py --out ref.json`).

Acceptance: agreement within ~1e-2 (reported as both max abs delta and max
relative delta; the verdict uses whichever tolerance is satisfied — oracle's
"~1e-2 relative or abs"). Also reports the vanilla-vs-bitlinear delta so the
oracle can see what the missing activation-RMSNorm/quant/biases cost.

Usage:
  python scripts/quantal_compare_logits.py rust.json ref.json
"""

import json
import sys

import numpy as np


def stats(name, a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    d = np.abs(a - b)
    denom = np.maximum(np.abs(b), 1.0)
    rel = d / denom
    return {
        "name": name,
        "n": int(a.size),
        "max_abs": float(d.max()),
        "mean_abs": float(d.mean()),
        "max_rel": float(rel.max()),
        "argmax_a": int(a.argmax()),
        "argmax_b": int(b.argmax()),
        "argmax_same": bool(a.argmax() == b.argmax()),
    }


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    rust_path, ref_path = sys.argv[1], sys.argv[2]
    rust = json.load(open(rust_path))
    ref = json.load(open(ref_path))

    assert len(rust["prompts"]) == len(ref["prompts"])
    ok_all = True
    for rp, fp in zip(rust["prompts"], ref["prompts"]):
        assert rp["n_tokens"] == fp["n_tokens"], (
            f"prompt {rp['prompt']} token count mismatch: "
            f"rust {rp['n_tokens']} vs ref {fp['n_tokens']}"
        )
        rs = stats(f"prompt {rp['prompt']} rust-vs-mlx-vanilla",
                   rp["logits"], fp["logits_vanilla"])
        print(json.dumps(rs))
        gate = rs["max_abs"] <= 1e-2 or rs["max_rel"] <= 1e-2
        ok_all &= gate
        print(f"  GATE {'PASS' if gate else 'FAIL'} "
              f"(max_abs={rs['max_abs']:.3e} max_rel={rs['max_rel']:.3e})")
        if "logits_bitlinear" in fp:
            bs = stats(f"prompt {rp['prompt']} rust-vs-mlx-bitlinear",
                       rp["logits"], fp["logits_bitlinear"])
            vs = stats(f"prompt {rp['prompt']} mlx-vanilla-vs-bitlinear",
                       fp["logits_vanilla"], fp["logits_bitlinear"])
            print(json.dumps(bs))
            print(json.dumps(vs))

    print("RESULT:", "PASS" if ok_all else "FAIL")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
