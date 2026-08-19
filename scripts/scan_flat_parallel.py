#!/usr/bin/env python3
"""Parallel streaming sentinel scan for the flat data/ dir (big files).

The part1 scan showed 432/1878 files carrying [PHONE] (33,198 hits) — the
shipped corpus is heavily damaged, so the scan must be fast. This variant
parallelizes curl streaming across N workers. Usage:

    uv run --script scan_flat_parallel.py [workers] [min-mb]   # default 4, 0
"""
# /// script
# dependencies = []
# ///

import json
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DATASET = "PeetPedro/cogitoergosumma-corpus"
SENTINELS = ("[PHONE]", "[EMAIL]", "[IP]")
TREE_BASE = f"https://huggingface.co/api/datasets/{DATASET}/tree/main"


def tree_files(sub: str) -> list[dict]:
    entries_all = []
    url = f"{TREE_BASE}/data%2F{sub}?limit=1000" if sub else f"{TREE_BASE}/data?limit=1000"
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": "sentinel-scan"})
        with urllib.request.urlopen(req, timeout=30) as r:
            entries = json.load(r)
            link = r.headers.get("Link", "")
        m = re.search(r"<([^>]+)>; rel=\"next\"", link)
        url = m.group(1) if m else None
        entries_all += [e for e in entries if e.get("type") == "file"]
    return entries_all


def scan_file(path: str) -> tuple[str, dict[str, int] | dict[str, str], float]:
    url = f"https://huggingface.co/datasets/{DATASET}/resolve/main/{path}"
    hits = {"[PHONE]": 0, "[EMAIL]": 0, "[IP]": 0}
    t0 = time.time()
    try:
        proc = subprocess.Popen(
            ["curl", "-sL", "--max-time", "600", url],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        assert proc.stdout is not None
        for raw in proc.stdout:
            try:
                line = raw.decode("utf-8", errors="ignore")
            except Exception:
                continue
            for s in SENTINELS:
                if s in line:
                    hits[s] += 1
        proc.wait(timeout=610)
    except Exception as e:  # noqa: BLE001
        return path, {"error": str(e)[:100]}, time.time() - t0
    return path, hits, time.time() - t0


def main() -> None:
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    min_mb = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    sub = sys.argv[3] if len(sys.argv) > 3 else ""
    files = tree_files(sub)
    files = [e for e in files if e.get("size", 0) / 1e6 >= min_mb]
    label = sub if sub else "flat"
    print(f"{label}: {len(files)} files (>= {min_mb}MB) with {workers} workers", flush=True)
    per_repo: dict[str, dict] = {}
    total = {"[PHONE]": 0, "[EMAIL]": 0, "[IP]": 0}
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(scan_file, e["path"]): e["path"] for e in files}
        for fut in as_completed(futs):
            path, hits, dt = fut.result()
            done += 1
            if "error" in hits:
                print(f"  ⚠ {path}: {hits['error']}", flush=True)
            elif any(hits.values()):
                name = path.removeprefix("data/")
                per_repo[name] = hits
                for s in SENTINELS:
                    total[s] += int(hits.get(s, 0))  # type: ignore[arg-type]
            if done % 200 == 0:
                print(f"  {done}/{len(files)} done, {len(per_repo)} hit, "
                      f"{time.time()-t0:.0f}s", flush=True)
    print(f"\n=== {label.upper()} SCAN RESULT ===", flush=True)
    print(f"total: PHONE {total['[PHONE]']} | EMAIL {total['[EMAIL]']} | "
          f"IP {total['[IP]']} | repos hit: {len(per_repo)}", flush=True)
    top = sorted(per_repo.items(), key=lambda kv: kv[1].get("[PHONE]", 0), reverse=True)[:15]
    for name, h in top:
        print(f"  {name}: {h}", flush=True)
    out = f"/tmp/sentinel-scan-{label}.json"
    with open(out, "w") as f:
        json.dump({"total": total, "per_repo": per_repo}, f, indent=1)
    print(f"saved {out}", flush=True)


if __name__ == "__main__":
    main()