---
name: plan-ceo-review
kind: command
version: 0.1.0
description: ceo + cfo two-voter council on a plan (business + cost lens).
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - ceo review this plan
  - business review
  - is this worth funding
  - plan ceo review
preferred-backends:
  - claude
roles_invoked:
  - ceo
  - cfo
---

## When to invoke

After `/office-hours` returned `experiment` or `ship-the-wedge` and you want
a second pair of eyes before committing engineering capacity. The CEO checks
whether the wedge still answers the six forcing questions; the CFO checks
whether the burn-rate is justified.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill plan-ceo-review \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill plan-ceo-review)
```

## Inputs

- Path to a PRD (typically the `/spec` output), OR
- Path to an `/office-hours` idea doc.

## Steps

1. **Adopt `ceo`** from `roles/ceo/SKILL.md`. Verify the plan still answers
   the six forcing questions (demand reality, status quo, specificity,
   wedge, falsifying obs, future-fit). If any answer drifted from the
   `/office-hours` doc, surface the drift.
2. **Adopt `cfo`** from `roles/cfo/SKILL.md`. Pull the most recent N entries
   from `~/.hivestack/guard/cost-ledger.jsonl` matching the project; estimate
   the spend on building this feature given current rates. Compare against
   the expected value the PRD claims.
3. **Emit both vote blocks** under a shared `## CEO + CFO council vote` heading.
4. **Apply charter rule** ([_charter.md](../../roles/_charter.md)): pass iff
   both ≥3 AND no `must_fix`. **Tie-break**: if CEO and CFO disagree by ≥2
   points, CEO casts the deciding vote (per charter).
5. **Write** the council notes to
   `~/.hivestack/projects/<slug>/decisions/ceo-review-<feature>-<YYYYMMDD-HHMM>.md`.

## Output

- Council notes artifact path.
- Both vote blocks.
- One-line verdict: pass | dissent | tie-broken-by-ceo.

## Failure modes

- PRD has no success metric: PM should have caught this; here it's an
  automatic `must_fix` from both voters.
- No cost-ledger data for this project: CFO can't estimate ROI; dissents
  with `must_fix: "no spend history to project against"`.
- Office-hours doc shows answers ≠ PRD answers: surface the drift, do NOT
  silently re-adopt the PRD's version.

## Hand-off

If `pass`: hand off to `/plan-eng-review`. If `dissent`: list `must_fix`,
stop. The author either revises the PRD or asks `/office-hours` to re-score
the underlying idea.
