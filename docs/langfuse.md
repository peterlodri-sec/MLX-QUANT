# Langfuse tracing (opt-in)

MLX-QUANT benchmarks can post run traces to a Langfuse instance — **only when
you opt in**. The helper lives in `scripts/langfuse_callback.py` (standard
library only, no new dependencies).

## Setup

```bash
export LANGFUSE_HOST=https://cloud.langfuse.com   # or your self-hosted instance
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
cd benchmarks/python
python bitlinear_bench.py
```

When all three `LANGFUSE_*` variables are set and non-empty:

- `langfuse_enabled()` returns `True`;
- the `@langfuse_trace_benchmark` decorator wraps the benchmark function,
  recording its name, wall time, and the first 200 characters of its result
  as a trace on `{LANGFUSE_HOST}/api/public/trace` (fire-and-forget daemon
  thread, all errors swallowed);
- `langfuse_trace(name, model=..., input_preview=..., output_preview=...,
  duration_ms=..., metadata=...)` is also available for manual tracing.

With any of the three variables unset the helper is a complete no-op: no
request is built, no thread is spawned, and the benchmark behaves exactly as
before.

## Relationship to the fleet's LiteLLM callback

The same env-var family powers the Langfuse callback in the crabcc LiteLLM
stack (`crabcc/install/ollama-stack/litellm.config.yaml`:
`success_callback` / `failure_callback: ["langfuse"]`). LiteLLM reads the
identical `LANGFUSE_HOST` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`
variables and posts to the same `/api/public/trace` ingestion endpoint — so
one set of credentials covers both LLM-server tracing and MLX-QUANT benchmark
tracing in the same Langfuse project.
