---
name: plan-eng-review
kind: command
version: 0.1.0
description: Engineering Manager reviews a PRD or plan and produces an ADR + risk list.
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - AskUserQuestion
triggers:
  - eng review this plan
  - architecture review
  - plan eng review
  - is the architecture sound
preferred-backends:
  - claude
  - codex
roles_invoked:
  - eng-manager
---

## When to invoke

After `/spec` produced a PRD, or whenever a plan is on the table that has architectural
or cross-service implications. Invoke proactively when the user proposes a new service,
a schema change, a migration, or a third-party integration.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill plan-eng-review 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill plan-eng-review)
```

## Inputs

- Path to a PRD or plan document (or paste the content).
- (Optional) target scale / SLO numbers.

## Steps

1. **Load `roles/eng-manager/SKILL.md`** and adopt the Engineering Manager persona.
2. **Read the input plan in full** before forming opinions.
3. **Scan the repo for context**: grep for existing services / modules that overlap
   with the proposed change. Cite `file:line` for any claim of overlap.
4. **Walk the 6-point architecture checklist** (failure surface, state boundaries,
   schema evolution, concurrency, reversibility, test seam). For each, write one
   paragraph of findings.
5. **Write an ADR** to:
   ```
   ~/.hivestack/projects/<slug>/decisions/ADR-<next-NNNN>-<topic>.md
   ```
   using the template in `roles/eng-manager/SKILL.md`. Status starts as `proposed`.
6. **Emit the vote block** (see `_charter.md`) at the end of the chat response.
7. **If verdict is `dissent`**, list `must_fix` items and stop. If `pass`, recommend
   the next step (typically: implement, then `/review`).

## Outputs

- ADR artifact path.
- Vote block in chat (yaml).
- One-line verdict.

## Failure modes

- Plan is too vague to architect: ask for the missing details, do not invent them.
- Plan proposes a tech the repo hasn't used: require an ADR-Alternatives section
  comparing to what's already in the stack.
- Plan ignores reversibility: must_fix unless the change is genuinely additive.

## Council expansion (M2)

When `architect` (M2) is wired, this command will run both as a 2-voter council. Until
then, the Eng Manager is the sole voter and may escalate to user on close calls.
