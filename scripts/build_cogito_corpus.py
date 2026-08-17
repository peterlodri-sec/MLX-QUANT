#!/usr/bin/env python3
"""build_cogito_corpus.py — THE CORPUS OF COGITOergoSUMMAsummarum

Collects text content from the `standardgalactic` GitHub user's public repos
into the PUBLIC HF bucket `PeetPedro/cogitoergosumma-corpus`.

Multiplexed: 4 parallel workers, each: shallow clone -> text-extract -> JSONL
-> delete clone -> `hf buckets cp` to the public bucket.

Conventions (workspace):
  - M1 disk is sacred: one repo at a time per worker, delete after processing.
  - text-only extensions; binary/heavy repos skipped.
  - hf CLI is logged in as PeetPedro (shell HF_TOKEN env may be invalid).
  - resumable: repos already in the bucket (or a local done-file) are skipped.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BUCKET = "PeetPedro/cogitoergosumma-corpus"
DATASET_REPO = "PeetPedro/cogitoergosumma-corpus"  # HF dataset repo (load_dataset-compatible)
OWNER = "standardgalactic"
STAGING = Path("/tmp/cogito-staging")
DONE_FILE = Path("/tmp/cogito-done.json")
MAX_WORKERS = 2  # "szépen lassan" — low parallelism, M1 disk is sacred
MAX_CLONE_MB = 300  # skip giant forks (chromium 21GB, coronavirus 37GB, ...):
                    # they're duplicate codebases, not original text, and would
                    # fill the M1 disk. Only small/medium forks are worth text.`

TEXT_EXTS = {
    ".txt", ".md", ".markdown", ".tex", ".org", ".rst", ".srt", ".vtt",
    ".tsv", ".json", ".py", ".sh", ".c", ".cpp", ".h", ".rs", ".go",
    ".java", ".js", ".ts", ".html", ".htm", ".yaml", ".yml", ".toml",
    ".csv", ".sql", ".rb", ".php", ".lua", ".r", ".jl",
}
SKIP_REPOS = {  # binary-heavy or non-unique content
    "fonts", "playfloor", "30-seconds-of-code", "tornado", "example",
    "dotfiles", "vimrc", "nvim", "config", "dot-config",
}
SKIP_BIN_EXT = {
    ".pdf", ".mhtml", ".mp3", ".wav", ".flac", ".png", ".jpg", ".jpeg",
    ".gif", ".webp", ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".woff", ".ttf", ".otf", ".eot", ".ico", ".mp4", ".mov", ".avi",
    ".pkl", ".npy", ".npz", ".h5", ".parquet", ".ipynb",
}


def gh_api(url: str) -> list:
    out = subprocess.run(
        ["gh", "api", url, "--paginate"],
        capture_output=True, text=True, timeout=60,
    )
    if out.returncode != 0:
        print(f"  [gh api error] {out.stderr[:200]}", flush=True)
        return []
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        # --paginate may concatenate multiple JSON arrays
        combined: list = []
        for chunk in re.findall(r"\[.*?\]", out.stdout, re.S):
            try:
                combined.extend(json.loads(chunk))
            except json.JSONDecodeError:
                pass
        return combined


def load_repos() -> list[dict]:
    # Priority: the FULL enumerated list (all 24k repos incl. forks), then the
    # non-fork list, then the partial cached list. Forks are processed too —
    # "szépen lassan" (slowly, low parallelism, disk-guarded).
    for src_name, src_path in (
        ("all (incl. forks)", "/tmp/cogito/repos_all.json"),
        ("non-fork", "/tmp/cogito/repos_nofork.json"),
        ("cached partial", "/tmp/cogito/all_repos.json"),
    ):
        p = Path(src_path)
        if p.exists():
            with open(p) as f:
                repos = json.load(f)
            print(f"[repos] loaded {len(repos)} repos from {p} ({src_name})", flush=True)
            break
    else:
        url = f"users/{OWNER}/repos?per_page=100&sort=updated"
        repos = gh_api(url)
        if not repos:
            print("  [error] no repos fetched — check gh auth", flush=True)
            sys.exit(1)
    # keep only text-relevant, non-skipped repos with size > 0
    keep = []
    for r in repos:
        name = r.get("name", "")
        if name in SKIP_REPOS:
            continue
        if r.get("size", 0) <= 0:
            continue
        keep.append(r)
    keep.sort(key=lambda r: -r.get("size", 0))
    print(f"[repos] {len(keep)} text-relevant repos (of {len(repos)} fetched)", flush=True)
    return keep


def load_done() -> set[str]:
    if DONE_FILE.exists():
        return set(json.loads(DONE_FILE.read_text()))
    return set()


def save_done(done: set[str]) -> None:
    DONE_FILE.write_text(json.dumps(sorted(done)))


def is_text(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return True
    if ext in SKIP_BIN_EXT:
        return False
    # unknown ext: sniff first bytes for nulls
    try:
        with open(path, "rb") as f:
            head = f.read(1024)
        if b"\x00" in head:
            return False
        return bool(re.search(rb"[a-zA-Z]{3,}", head))
    except OSError:
        return False


def disk_free_gb() -> float:
    out = subprocess.run(["df", "-k", "/"], capture_output=True, text=True)
    try:
        # df -k: last column is available KB
        line = out.stdout.strip().split("\n")[-1]
        parts = [p for p in line.split() if p]
        return float(parts[3]) / (1024 * 1024)
    except (IndexError, ValueError):
        return 10.0  # unknown → assume ok


def process_repo(repo: dict, worker: int, done: set[str]) -> dict | None:
    name = repo["name"]
    if name in done:
        return {"name": name, "status": "skip-done"}
    size_mb = repo.get("size", 0) / 1024
    if size_mb > MAX_CLONE_MB:
        print(f"[w{worker}]   ∎ {name}: {size_mb:.0f} MB > {MAX_CLONE_MB} MB cap — skipped "
              f"(giant fork, not original text, M1 disk sacred)", flush=True)
        return {"name": name, "status": "skip-too-big"}
    clone_dir = STAGING / f"w{worker}" / name
    out_jsonl = STAGING / f"w{worker}" / f"{name}.jsonl"
    clone_dir.parent.mkdir(parents=True, exist_ok=True)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print(f"[w{worker}] ▶ {name} ({size_mb:.0f} MB per API) cloning…", flush=True)
    # disk guard: the GitHub API size is unreliable (a 157MB repo cloned to
    # 10GB — LFS/binary). Wait for >=3GB free before EVERY clone so parallel
    # workers never overflow the M1 disk.
    while disk_free_gb() < 3.0:
        print(f"[w{worker}]   … {name}: waiting for disk ({disk_free_gb():.1f}GB free)", flush=True)
        time.sleep(15)
    try:
        r = subprocess.run(
            ["git", "clone", "--depth", "1", "-q",
             f"https://github.com/{OWNER}/{name}.git", str(clone_dir)],
            capture_output=True, text=True, timeout=600,
        )
        if r.returncode != 0:
            print(f"[w{worker}]   ✗ {name}: clone failed: {r.stderr[:150]}", flush=True)
            return {"name": name, "status": "clone-fail", "error": r.stderr[:150]}
    except subprocess.TimeoutExpired:
        print(f"[w{worker}]   ✗ {name}: clone timeout", flush=True)
        return {"name": name, "status": "clone-timeout"}

    files, chars, rows = 0, 0, 0
    with open(out_jsonl, "w") as f:
        for p in sorted(clone_dir.rglob("*")):
            if not p.is_file() or ".git" in p.parts:
                continue
            if not is_text(p):
                continue
            rel = str(p.relative_to(clone_dir))
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if len(text) < 40:
                continue
            files += 1
            chars += len(text)
            rows += 1
            f.write(json.dumps({"id": f"{name}/{rel}", "text": text, "source": name}) + "\n")

    # cleanup clone immediately (M1 disk sacred)
    subprocess.run(["rm", "-rf", str(clone_dir)], capture_output=True)

    if rows == 0:
        out_jsonl.unlink(missing_ok=True)
        print(f"[w{worker}]   ∅ {name}: no text content", flush=True)
        return {"name": name, "status": "no-text"}

    # upload to the HF DATASET repo (not the bucket) — the user wants the
    # corpus loadable via datasets.load_dataset(). The JSONL is local staging,
    # so this costs zero extra M1 disk. The bucket remains the archive.
    dest = f"data/{name}.jsonl"
    print(f"[w{worker}]   ↑ {name}: {rows} rows, {chars/1e6:.1f} MB text → {DATASET_REPO}:{dest}", flush=True)
    up = subprocess.run(
        ["hf", "upload", DATASET_REPO, str(out_jsonl), dest, "--repo-type", "dataset"],
        capture_output=True, text=True, timeout=600,
    )
    if up.returncode != 0:
        print(f"[w{worker}]   ✗ {name}: upload failed: {up.stderr[:200]}", flush=True)
        return {"name": name, "status": "upload-fail", "error": up.stderr[:200]}

    out_jsonl.unlink(missing_ok=True)
    done.add(name)
    save_done(done)
    print(f"[w{worker}]   ✓ {name}: {rows} rows, {chars/1e6:.1f} MB, {time.time()-t0:.0f}s", flush=True)
    return {"name": name, "status": "ok", "rows": rows, "chars": chars}


def main() -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    done = load_done()
    repos = load_repos()
    # skip already-uploaded (done-file) repos
    pending = [r for r in repos if r["name"] not in done]
    print(f"[main] {len(pending)} repos to process across {MAX_WORKERS} workers", flush=True)

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {
            ex.submit(process_repo, r, i % MAX_WORKERS, done): r["name"]
            for i, r in enumerate(pending)
        }
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:  # noqa: BLE001
                print(f"[main] worker error: {e}", flush=True)

    ok = [r for r in results if r and r["status"] == "ok"]
    print(f"\n[main] done: {len(ok)} ok, {len(results)-len(ok)} failed/skipped", flush=True)
    print(f"[main] bucket: hf://buckets/{BUCKET} (public)", flush=True)


if __name__ == "__main__":
    main()
