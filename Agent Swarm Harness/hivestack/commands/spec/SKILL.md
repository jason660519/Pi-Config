---
name: spec
kind: command
version: 0.1.0
description: PM writes a PRD from an approved idea, ready for plan-eng-review.
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - write a spec
  - write a prd
  - spec this feature
  - turn this into a spec
preferred-backends:
  - claude
roles_invoked:
  - pm
---

## When to invoke

After `/office-hours` returned `experiment` or `ship-the-wedge`, or when the user
directly asks for a PRD. Invoke proactively when the user says "let's spec X" or
"write a PRD for X".

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill spec 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill spec)
```

## Inputs

- A feature name or idea slug.
- (Optional) the artifact path from a prior `/office-hours` run.

## Steps

1. **Load `roles/pm/SKILL.md`** and adopt the PM persona. Stay in PM lane only.
2. **If an `/office-hours` artifact exists, read it first.** Pull problem, user, and
   metric from there.
3. **Fill the PRD template** from `roles/pm/SKILL.md`. For each section the user
   hasn't already answered, ask via `AskUserQuestion`. Required answers:
   - Problem (one sentence).
   - User (persona + moment).
   - Success metric (current → target).
   - Scope in / out (bullets).
   - Acceptance criteria (Given / When / Then).
   - Risks.
   - Rollout (flag, audience, kill switch, owner).
4. **Refuse to ship** if the user cannot name a success metric. Say so and stop.
5. **Write the PRD** to:
   ```
   ~/.hivestack/projects/<slug>/specs/<feature-slug>-<YYYYMMDD-HHMM>.md
   ```
6. **State next step**: run `/plan-eng-review <spec-path>`.

## Outputs

- PRD artifact path.
- The PRD's success metric and scope (bulleted) repeated in chat for confirmation.

## Failure modes

- Vanity metric (clicks, signups without retention): PM dissents, ask for a behaviour-
  change metric.
- Scope creep mid-spec: PM moves items to "scope (out)" and surfaces them.
- Missing acceptance criteria: PM refuses to save the PRD.

## Hand-off

After this command, the natural next step is `/plan-eng-review` to bring the
Engineering Manager in.
