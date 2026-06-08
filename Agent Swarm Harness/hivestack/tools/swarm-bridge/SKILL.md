---
name: swarm-bridge
kind: tool
version: 0.2.0
description: Multi-agent router — Claude / Codex / Gemini / local OSS, with driver YAML config.
allowed-tools:
  - Bash
  - Read
triggers:
  - run on codex
  - run on gemini
  - pair this
  - dispatch to
preferred-backends:
  - claude
---

## What it is

The piece that turns "hivestack is Claude-only" into "hivestack routes work
to whichever backend fits". v0.2 ships a working **driver loader** + **real
dispatch** for any CLI-shaped backend, plus a `mock` driver for tests.

Drivers are declared in `agents/<name>.yaml`. `list-backends` lists what's
configured + healthy; `route <role> <prompt>` picks by role affinity;
`run --backend <name> <prompt>` invokes a specific one; `cost-quote`
estimates USD before you commit.

## CLI

```bash
swarm-bridge route <role> <prompt>                # dispatch by role affinity
swarm-bridge run --backend <name> <prompt>        # invoke a specific driver
swarm-bridge list-backends                        # configured + healthy
swarm-bridge health <backend>                     # ping + capability probe
swarm-bridge cost-quote --backend <name> <prompt> # estimate USD before running
swarm-bridge version
```

## Driver config

`agents/<provider>.yaml` (one file per backend). The shipped set:

| File | Kind | Notes |
|---|---|---|
| `agents/claude.yaml` | cli | `claude` binary, `--print` for headless one-shot |
| `agents/codex.yaml` | cli | `codex --mode headless`; needs `OPENAI_API_KEY` |
| `agents/mock.yaml` | mock | always healthy, returns canned response |

Schema:

```yaml
name: codex
kind: cli                # cli | mock | acp | mcp | http (only cli + mock are live in v0.2)
binary: codex
args: ["--mode", "headless"]
env:
  OPENAI_API_KEY: "${OPENAI_API_KEY}"
capabilities: [code_edit, shell]
cost_per_mtok_in: 5.0
cost_per_mtok_out: 15.0
context_window: 200000
role_affinity: [backend-eng, data-eng]
```

## Routing rules

1. **Role affinity** — each role lists `preferred_backends`; bridge picks
   the first healthy one in that list.
2. **Capability match** — task needs `browse` capability? skip backends that
   don't claim it.
3. **Cost ceiling** — consult `swarm-guard budget status`; if `remaining <
   cost-quote`, refuse OR fall back to a cheaper backend (the `/pair`
   command surfaces this to the user via `AskUserQuestion`).
4. **Ensemble (M4)** — high-risk gate (`/cso`, `/ship`) can specify
   `--ensemble 3` to run on 3 backends and majority-vote. Not in v0.2.

## Live as of v0.2

- ✅ `list-backends` reads all `agents/*.yaml`
- ✅ `health` checks PATH for `cli` kind, returns `true` for `mock`
- ✅ `run --backend <name>` invokes the binary with the prompt argv and
      env from the YAML, captures stdout/stderr/rc/elapsed_ms
- ✅ `route <role>` picks by `role_affinity` then falls through to mock
- ✅ `cost-quote` estimates USD with the rule-of-thumb 4 chars/token

Not yet live (M4):

- ❌ ACP / MCP / HTTP driver kinds
- ❌ Long-running daemon per backend (every dispatch re-launches)
- ❌ Ensemble mode + majority vote
- ❌ Streaming response

## Storage

```
~/.hivestack/analytics/tool-usage.jsonl   per-call event (opt-in)
~/.hivestack/guard/cost-ledger.jsonl      caller's responsibility (via /pair etc.)
```

## Roadmap

- M2.5 (this) — driver loader + claude + codex + mock drivers
- M3 — ACP / MCP driver kinds; long-running daemon per backend
- M4 — ensemble + majority vote on `/ship` gate
