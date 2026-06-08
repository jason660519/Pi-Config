---
name: benchmark
kind: command
version: 0.1.0
description: perf-eng runs benchmarks against a baseline and decides regression.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Write
  - AskUserQuestion
triggers:
  - benchmark
  - perf regression
  - is this fast enough
preferred-backends:
  - claude
roles_invoked:
  - perf-eng
tools_invoked:
  - swarm-bench
---

## When to invoke

After implementing any change in a hot path, before `/ship` when an SLO is
documented in the PRD, or when investigating a perf regression in production.
Invoke proactively when the user says "is this fast enough?" or "perf
regression on X".

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill benchmark \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill benchmark)
```

## Inputs

- `<target>` — what to bench (a function path, an endpoint, a suite name).
- (Optional) `--baseline <run-id>` — compare against a specific prior run.
  Default: most recent baseline for the same target.
- (Optional) `--slo <metric=value>` — e.g., `p95=20ms`. Refuse to run if no
  SLO is provided AND no PRD-documented SLO exists.

## Steps

1. **Adopt `perf-eng`** from `roles/perf-eng/SKILL.md`.
2. **Define "enough"** — capture the SLO (from `--slo` or PRD); refuse if
   absent.
3. **Run baseline** (current main):
   ```bash
   ~/.claude/skills/hivestack/tools/swarm-bench/bin/swarm-bench run <suite>
   # v0.5: stub mode — prints planned actions; M3 wires real runner
   ```
4. **Run candidate** (current HEAD) with the same harness, warmup, dataset.
5. **Report**: baseline p50/p95/p99/max, candidate same, delta + statistical
   significance (note: significance check is M3, until then state "candidate
   N=3 vs baseline N=3" and let user judge).
6. **Write** the report to
   `~/.hivestack/projects/<slug>/bench/<target>-<YYYYMMDD-HHMM>.md`.
7. **Emit the vote block** per `roles/perf-eng/SKILL.md`.

## Output

- Bench report artifact path.
- Vote block (`must_fix` if p95 regressed >5% with no explicit accept).

## Failure modes

- swarm-bench not installed: refuse with install instructions.
- No SLO in PRD AND no `--slo` flag: refuse — perf without a target is
  theatre.
- Baseline too old (>24h): re-run baseline first.

## Hand-off

If `pass`: continue. If `dissent` and the regression is intentional (e.g.,
correctness fix that requires more compute), ask the user to add an
"accepted regression" note to the PRD with reason; perf-eng then re-votes
`pass` with `should_consider`.
