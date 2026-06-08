---
name: cost-report
kind: command
version: 0.1.0
description: cfo aggregates the cost ledger into per-session/day/skill rolls.
allowed-tools:
  - Bash
  - Read
  - Write
triggers:
  - cost report
  - what did this cost
  - budget status
  - cfo report
preferred-backends:
  - claude
roles_invoked:
  - cfo
---

## When to invoke

End of a sprint or at the start of `/plan-ceo-review` when you want the CFO
to ground their vote in actual spend data. Invoke when the user asks "what
did this cost?" or "is the burn-rate healthy?".

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill cost-report \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill cost-report)
```

## Inputs

- (Optional) `--since <YYYY-MM-DD>` — date floor.
- (Optional) `--by <session|day|skill|all>` — grouping. Default: `all`.

## Steps

1. **Adopt `cfo`** from `roles/cfo/SKILL.md`.
2. **Run** the rollup:
   ```bash
   ~/.claude/skills/hivestack/bin/hivestack-cost-report \
     ${SINCE:+--since "$SINCE"} ${BY:+--by "$BY"}
   ```
3. **Interpret**: surface top-3 spend lines by session and by skill. Compare
   to the current budget (`current_budget` field in the JSON) and flag if
   any session went over.
4. **Spike detection**: compare today's per-skill spend to the 7-day average
   for the same skill (if rollup data available). >50% jump → must_fix on
   the next `/plan-ceo-review`.
5. **Write** the report to
   `~/.hivestack/projects/<slug>/cost/<YYYYMMDD-HHMM>.md`.

## Output

- Cost report artifact path.
- Top-3 lines by session, by skill.
- Budget status (over / under / unset).
- One-paragraph CFO note.

## Failure modes

- Empty ledger: print the note ("no cost-ledger yet — call `swarm-guard cost
  log`") and exit 0. Don't fabricate a report.
- Malformed rows: skip silently; count of skips appended to the report.

## Convention for attribution

The CFO can only attribute spend to a skill if `swarm-guard cost log` was
called with a description that starts with `<skill>:`. The convention is:

```bash
hivestack-cost-log 0.42 "review: claude opus 800k tokens"
```

Skills that don't follow the convention show up under `"by_skill": {}` —
visible signal that the call site needs a description fix.
