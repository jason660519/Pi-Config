---
name: plan-design-review
kind: command
version: 0.1.0
description: designer + accessibility-lead two-voter council on a design plan.
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - design review this plan
  - plan design review
  - is the design ready
preferred-backends:
  - claude
roles_invoked:
  - designer
  - accessibility-lead
---

## When to invoke

After `/spec` produces a PRD that includes UI scope, or whenever a Figma /
mockup / built screen is on the table for sign-off. Invoke proactively when
the user shares a mockup URL or asks "does this design work?".

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill plan-design-review \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill plan-design-review)
```

## Inputs

- Path to a PRD with a UI scope section, OR
- URL / path to a rendered mockup, OR
- A screen the user is iterating on.

## Steps

1. **Adopt `designer`** from `roles/designer/SKILL.md`. Run the critique
   checklist (one primary action, all three states, copy, hierarchy, hit
   targets, motion).
2. **Adopt `accessibility-lead`** from `roles/accessibility-lead/SKILL.md`.
   Run the audit checklist (tab order, markup roles, labels, landmarks, live
   regions, contrast, reduced motion).
3. **Emit both vote blocks** under a shared `Design council vote` heading.
4. **Apply charter rule** ([_charter.md](../../roles/_charter.md)): pass iff
   both ≥3 AND no `must_fix`.
5. **Write** the council notes to
   `~/.hivestack/projects/<slug>/design-reviews/<feature>-<YYYYMMDD-HHMM>.md`.

## Output

- Council notes artifact path.
- Both vote blocks.
- One-line verdict: pass | dissent (+ blockers).

## Failure modes

- No mockup / screen yet: refuse — designer dissents, asks for at least HTML.
- WCAG contrast failure: must_fix from accessibility-lead, blocks pass even
  if designer is happy.

## Hand-off

If `pass`: hand off to `frontend-eng` for implementation, then `/review`,
then `/qa`. If `dissent`: list blockers, stop.
