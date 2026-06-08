---
name: office-hours
kind: command
version: 0.1.0
description: CEO office hours — six forcing questions before any code is written.
allowed-tools:
  - Bash
  - Read
  - Write
  - WebSearch
  - AskUserQuestion
triggers:
  - office hours
  - is this worth building
  - help me think through
  - i have an idea
preferred-backends:
  - claude
roles_invoked:
  - ceo
---

## When to invoke

Use **before** writing a PRD, before any code, before any architecture talk. The user
has an idea and wants to know whether to spend the next 2–4 weeks on it. Invoke
proactively (do NOT just answer directly) when the user describes a new product idea,
asks "should I build X", or is exploring a concept that doesn't exist yet.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill office-hours 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill office-hours)
```

## Inputs

- A single sentence idea, or a paragraph dump.
- (Optional) link to a competitor or prior art.

## Steps

1. **Load `roles/ceo/SKILL.md`** and adopt the CEO persona. Stay in CEO lane only.
2. **Ask the six forcing questions** from the CEO playbook, one at a time using
   `AskUserQuestion`. Do not batch them — each answer changes the next question.
3. **Score the idea** after all six are answered:
   - 5: ship the wedge this week.
   - 3–4: needs one cheap experiment to falsify before committing.
   - 1–2: kill or shelve.
4. **Write the artifact** to:
   ```
   ~/.hivestack/projects/<slug>/ideas/<topic-slug>-<YYYYMMDD-HHMM>.md
   ```
   Use the schema below.
5. **State the verdict** in the chat in one sentence and link to the artifact.

## Artifact schema

```markdown
# Idea: <one-line>

Date: <YYYY-MM-DD HH:MM>
CEO score: <1-5>
Verdict: <kill | experiment | ship-the-wedge>

## Six questions
1. Demand reality — <answer>
2. Status quo — <answer>
3. Desperate specificity — <answer>
4. Narrowest wedge — <answer>
5. Observation that would falsify — <answer>
6. Future-fit — <answer>

## Cheapest next experiment
<one paragraph — what we'd learn in <1 week and how>

## Handoff
- If `experiment` or `ship-the-wedge`: run `/spec <topic>` next.
- If `kill`: log the kill reason and stop.
```

## Outputs

- Artifact path printed to chat.
- One-line verdict.

## Failure modes

- User refuses to name a specific user: surface the gap and recommend killing or
  doing customer discovery first.
- User has already started building: still run the six questions; if score <3,
  recommend stopping and writing a kill-or-pivot doc.

## Telemetry event

Logs `{"skill":"office-hours","verdict":"<kill|experiment|ship>"}` to
`~/.hivestack/analytics/skill-usage.jsonl` when telemetry is on.
