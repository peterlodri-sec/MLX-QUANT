#!/usr/bin/env bash
# cogito-status.sh — 5-minute progress/status reporter for the standardgalactic
# corpus build (cogitoergosumma-corpus → HF dataset + bucket archive).
# Usage: ./cogito-status.sh        (one-shot)
#        watch -n300 ./cogito-status.sh   (every 5 min)
set -uo pipefail
export PATH="/opt/homebrew/bin:$PATH"

ts() { date +%H:%M:%S; }
LINE="[$(ts)]"

# build process — find any live build_cogito_corpus.py (PID changes every run)
BPID=$(pgrep -f "build_cogito_corpus.py" | head -1 || echo "")
if [ -n "$BPID" ]; then
  LINE="$LINE build=ALIVE(pid $BPID)"
else
  LINE="$LINE build=DIED"
fi

# progress from the done-file (source of truth; survives log deletion)
DONE=$(python3 -c "import json; print(len(json.load(open('/tmp/cogito-done.json'))))" 2>/dev/null || echo 0)
LINE="$LINE | done=$DONE"

# staging backlog
STAGE=$(du -sh /tmp/cogito-staging 2>/dev/null | cut -f1 || echo 0)
LINE="$LINE | staging=$STAGE"

# disk
FREE=$(df -h / | tail -1 | awk '{print $4}')
LINE="$LINE | disk-free=$FREE"

# bucket archive + dataset repo file count
BINFO=$(timeout 15 hf buckets info PeetPedro/cogitoergosumma-corpus 2>/dev/null \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(f"{d.get(\"total_files\",0)} files {round(d.get(\"size\",0)/1e9,2)}GB")' 2>/dev/null || echo "?")
LINE="$LINE | bucket=$BINFO"

DFILES=$(timeout 15 hf download PeetPedro/cogitoergosumma-corpus --repo-type dataset \
  --local-dir /tmp/cogito-ds-count 2>/dev/null; find /tmp/cogito-ds-count -name "*.jsonl" 2>/dev/null | wc -l)
rm -rf /tmp/cogito-ds-count
LINE="$LINE | dataset-jsonl=$DFILES"

echo "$LINE"
