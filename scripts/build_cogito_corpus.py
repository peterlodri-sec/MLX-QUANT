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
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BUCKET = "PeetPedro/cogitoergosumma-corpus"
DATASET_REPO = "PeetPedro/cogitoergosumma-corpus"  # HF dataset repo (load_dataset-compatible)
OWNER = "standardgalactic"
STAGING = Path("/tmp/cogito-staging")
DONE_FILE = Path("/tmp/cogito-done.json")
MAX_WORKERS = 2      # extractor workers: clone + extract -> queue
UPLOAD_WORKERS = 2   # parallel uploaders (4 was too aggressive → HF rate-limit pileup)
upload_queue: "queue.Queue" = queue.Queue()  # Path objects of finished JSONLs
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
    # known LFS-monsters: the GitHub API says ~157MB but the clone is 8.7GB
    # (binary/LFS payload) — they deadlock the disk guard. Skip by name.
    "AEC-Challenge", "covid-19-repo-data", "chromium", "coronavirus_structural_task_force",
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


# ── minimal PII + secret scrubbing (before anything is written to the corpus) ──
_SECRET_PATTERNS = [
    # well-known API key / token shapes (highest confidence, low false-positive)
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "SK-API-KEY"),
    (re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"), "GITHUB-TOKEN"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS-ACCESS-KEY"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}[A-Za-z0-9/+]{32,}\b"), "AWS-SECRET"),
    (re.compile(r"\bhf_[A-Za-z0-9]{10,}\b"), "HF-TOKEN"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "SLACK-TOKEN"),
    (re.compile(r"\bBearer [A-Za-z0-9._~+/-]{20,}\b", re.I), "BEARER-TOKEN"),
    (re.compile(r"\b(?:ssh|git)://[A-Za-z0-9._%+-]+:[^@\s/]+@", re.I), "URL-CREDENTIAL"),
    # PEM private keys (any type)
    (re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----", re.S), "PRIVATE-KEY"),
    # crypto wallet addresses (EVM-style)
    (re.compile(r"\b0x[a-fA-F0-9]{40}\b"), "WALLET-ADDRESS"),
    # PII
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "EMAIL"),
    (re.compile(r"\b\+?[0-9]{1,3}[ .-]?\(?[0-9]{2,4}\)?[ .-]?[0-9]{3,4}[ .-]?[0-9]{3,4}\b"), "PHONE"),
    (re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"), "IP"),
]


def scrub_text(text: str) -> str:
    """Redact minimal PII + secrets before a file lands in the corpus.
    Conservative: only well-formed token/secret/credential shapes are replaced,
    so ordinary code (test@example.com, 127.0.0.1) is NOT mangled."""
    for pat, label in _SECRET_PATTERNS:
        text = pat.sub(f"[{label}]", text)
    return text


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
    # 10GB — LFS/binary). Wait for >=8GB free before EVERY clone so parallel
    # workers never overflow the M1 disk (the machine can't sustain 15GB free
    # during cloning — user picked 8GB as the balance).
    while disk_free_gb() < 8.0:
        print(f"[w{worker}]   … {name}: waiting for disk ({disk_free_gb():.1f}GB free, need 8)", flush=True)
        time.sleep(15)
    try:
        r = subprocess.run(
            ["git", "clone", "--depth", "1", "-q",
             f"https://github.com/{OWNER}/{name}.git", str(clone_dir)],
            capture_output=True, text=True, timeout=600,
        )
        if r.returncode != 0:
            # cleanup the partial clone immediately — this is what caused 19GB
            # of stale clones to pile up on the M1 disk across failed clones
            subprocess.run(["rm", "-rf", str(clone_dir)], capture_output=True)
            print(f"[w{worker}]   ✗ {name}: clone failed: {r.stderr[:150]}", flush=True)
            return {"name": name, "status": "clone-fail", "error": r.stderr[:150]}
    except subprocess.TimeoutExpired:
        subprocess.run(["rm", "-rf", str(clone_dir)], capture_output=True)
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
            text = scrub_text(text)  # PII + secret redaction before the corpus
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

    # Hand the finished JSONL to the shared upload queue — the uploaders run
    # in their own parallel pool, so this worker immediately starts the next
    # clone instead of blocking on a (possibly slow) single-threaded upload.
    upload_queue.put(out_jsonl)
    print(f"[w{worker}]   → {name}: {rows} rows, {chars/1e6:.1f} MB text queued for upload "
          f"(queue depth {upload_queue.qsize()})", flush=True)
    return {"name": name, "status": "extracted", "rows": rows, "chars": chars}


# ── uploader: batched directory sync (1 HF call moves ALL staged JSONLs).
# Per-file `hf upload` calls hit HF rate-limits hard (every upload was 429'd).
# A single `hf upload <dir>` commits the whole batch — one HTTP round-trip.
def upload_worker(worker: int, done: set[str], results: list, stop: threading.Event) -> None:
    last_sync = 0.0
    sync_dir = STAGING.parent / "cogito-sync"
    while True:
        # final drain when told to stop; otherwise keep cycling
        if stop.is_set():
            break
        # wait for a batch to accumulate, then sync the whole staging dir
        time.sleep(10)
        try:
            batch = [p for w in ("w0", "w1") for p in (STAGING / w).glob("*.jsonl")]
        except OSError:
            continue
        if not batch:
            continue
        # only sync files that are "settled" (mtime > 5s — no extractor mid-write)
        settled = []
        for p in batch:
            try:
                if time.time() - p.stat().st_mtime > 5:
                    settled.append(p)
            except OSError:  # file vanished (extractor deleted a no-text jsonl)
                continue
        # sync whatever is settled; leave fresh files for the next cycle
        # (waiting for the WHOLE batch to settle never fires — extractors
        # keep writing new files, so there is always a fresh one)
        if not settled:
            continue
        if time.time() - last_sync < 15:  # min interval between HF commits
            continue
        last_sync = time.time()
        n = len(settled)
        total_mb = 0.0
        # hardlink the settled files into a dedicated sync dir so we upload
        # ONLY those files, never the whole staging (which grows while we
        # upload and made each sync take minutes).
        sync_dir.mkdir(parents=True, exist_ok=True)
        linked = []
        for p in settled:
            try:
                total_mb += p.stat().st_size / 1e6
                dst = sync_dir / p.name
                if dst.exists():
                    dst.unlink()
                os.link(p, dst)  # hardlink: same FS, zero copy
                linked.append(dst)
            except OSError:
                continue
        if not linked:
            continue
        print(f"[u{worker}]   ⤒ syncing {n} files ({total_mb:.1f} MB) → {DATASET_REPO}:data/ (batched)", flush=True)
        try:
            up = subprocess.run(
                ["hf", "upload", DATASET_REPO, str(sync_dir), "data", "--repo-type", "dataset"],
                capture_output=True, text=True, timeout=900,
            )
        except subprocess.TimeoutExpired:
            print(f"[u{worker}]   ↻ sync timeout — will retry next cycle", flush=True)
            continue
        if up.returncode != 0:
            print(f"[u{worker}]   ↻ sync failed: {up.stderr[:150]} — retry next cycle", flush=True)
            time.sleep(60)  # HF rate-limit backoff between sync attempts
            continue
        # success: mark every staged file as done and remove it
        for p in settled:
            name = p.stem
            done.add(name)
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
        # clear the sync dir (the links point at the now-deleted files anyway)
        for d in linked:
            try:
                d.unlink(missing_ok=True)
            except OSError:
                pass
        save_done(done)
        results.append({"name": f"batch-{int(last_sync)}", "status": "ok", "mb": total_mb, "n": n})
        print(f"[u{worker}]   ✓ synced {n} files ({total_mb:.1f} MB)", flush=True)


def main() -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    done = load_done()
    repos = load_repos()
    # skip already-uploaded (done-file) repos
    pending = [r for r in repos if r["name"] not in done]
    print(f"[main] {len(pending)} repos to process across {MAX_WORKERS} workers", flush=True)

    results = []  # extractor results
    upload_results = []  # uploader results
    stop = threading.Event()
    # one batched sync-uploader: drains the whole staging dir per HF commit
    uploader_fut = ThreadPoolExecutor(max_workers=1).submit(upload_worker, 0, done, upload_results, stop)
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

    # tell the sync-uploader to stop; it does a final drain then exits
    stop.set()
    try:
        uploader_fut.result(timeout=1800)
    except Exception as e:  # noqa: BLE001
        print(f"[main] uploader error: {e}", flush=True)

    extracted = [r for r in results if r and r["status"] == "extracted"]
    ok_up = [r for r in upload_results if r and r["status"] == "ok"]
    fail_up = [r for r in upload_results if r and r["status"] != "ok"]
    print(f"\n[main] extracted: {len(extracted)} | uploaded OK: {len(ok_up)} | "
          f"upload failed: {len(fail_up)} | failed/skipped: {len(results)-len(extracted)}",
          flush=True)
    print(f"[main] dataset: {DATASET_REPO} (public, load_dataset-ready) | "
          f"bucket archive: hf://buckets/{BUCKET}", flush=True)


if __name__ == "__main__":
    main()
