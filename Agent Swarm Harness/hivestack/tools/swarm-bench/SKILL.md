---
name: swarm-bench
kind: tool
version: 0.2.0
description: Benchmark agents/drivers across a task suite via swarm-bridge.
allowed-tools:
  - Bash
  - Read
triggers:
  - benchmark this
  - bench models
  - run leaderboard
preferred-backends:
  - claude
---

## What it is

The `perf-eng` role's measurement harness. v0.2 ships a working runner that
dispatches a YAML-declared task suite through `swarm-bridge` against one or
more backends, captures per-task elapsed_ms + rc, and writes a per-run
summary.

LLM-as-judge quality scoring is M3 (needs a judge prompt + a scoring
backend). Until then, the runner reports execution-success + latency only.

## CLI

```bash
swarm-bench run <suite> [--backends <comma-separated>]
swarm-bench list-suites
swarm-bench leaderboard [--limit N]
swarm-bench compare <run-a-id> <run-b-id>
swarm-bench version
```

## Suite schema

`~/.hivestack/bench/suites/<name>.yaml`:

```yaml
name: regression-smoke
backends: [claude, mock]                # default if --backends not passed
tasks:
  - id: simple-add
    prompt: "Write a Python function that adds two integers and returns the sum."
  - id: bug-find
    prompt: "Review this diff for off-by-one bugs: ..."
```

A task entry can also be a bare string (then `id` is its first 40 chars).

## Live as of v0.2

- ✅ Suite loader (uses the same tiny YAML reader as swarm-bridge)
- ✅ Runner — dispatches each `task × backend` pair through swarm-bridge,
      writes one JSON per call to `~/.hivestack/bench/runs/<run-id>/`
- ✅ Per-run `summary.json` with per-backend `n / ok / p50_ms / max_ms`
- ✅ `leaderboard` reads the last N runs' summaries; `compare` diffs two
- ✅ Example suite shipped at `~/.hivestack/bench/suites/example.yaml`
      (created on first `swarm-bench list-suites` if missing)

Not yet:

- ❌ LLM-as-judge quality scoring — M3
- ❌ Statistical significance check (Mann-Whitney) — M3
- ❌ HTML leaderboard render (currently JSON only) — M3

## Storage

```
~/.hivestack/bench/
├── suites/<name>.yaml             task definitions
└── runs/<run-id>/
      ├── <backend>--<task>.json   per-task result
      └── summary.json
```

## Roadmap

- M2.5 (this) — runner + summary + leaderboard JSON
- M3 — LLM-judge quality + Mann-Whitney significance
- M3 — HTML leaderboard render via swarm-pdf
- M4 — telemetry rollup ties bench results to /cost-report
