---
name: review
kind: command
version: 0.1.0
description: Senior Code Reviewer scans the current git diff for bugs, reuse, and efficiency.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - AskUserQuestion
triggers:
  - review this
  - code review
  - review the diff
  - any bugs
preferred-backends:
  - claude
  - codex
roles_invoked:
  - code-reviewer
---

## When to invoke

After implementation work and before `/ship`. Invoke proactively when the user finishes
a feature and asks "is this good?" or "anything I missed?". Also invoke when the user
explicitly types `/review`.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill review 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill review)
```

## Inputs

- (Optional) `--base <ref>`: review diff against this ref. Default: `main` or `master`.
- (Optional) file paths to scope the review.

## Steps

1. **Load `roles/code-reviewer/SKILL.md`** and adopt the Senior Code Reviewer persona.
2. **Gather the diff**:
   ```bash
   BASE="${BASE:-$(git rev-parse --verify main 2>/dev/null || git rev-parse --verify master 2>/dev/null || echo HEAD~1)}"
   git diff --stat "${BASE}"...HEAD
   git diff "${BASE}"...HEAD
   ```
   Also list untracked files (`git ls-files --others --exclude-standard`) — they
   often contain the new code under review.
3. **Read the full diff once** before forming opinions. Do not start finding issues yet.
4. **For each changed file**: state in one sentence what the change *intended* to do,
   then look in the surrounding repo for the failure mode that would falsify the intent.
5. **For each finding**: produce the `Finding format` block from the role SKILL.md.
   Rank by severity (`bug` > `smell` > `nit`). Skip `nit` if there are >5 — leave
   them for the formatter.
6. **Write the review** to:
   ```
   ~/.hivestack/projects/<slug>/reviews/<branch>-<YYYYMMDD-HHMM>.md
   ```
7. **Emit the vote block** at the end of the chat response.
8. **If `--comment` flag**: not implemented in M1 (lands in M2 with `gh pr review`).

## Outputs

- Review artifact path.
- Top 3 findings inline in chat.
- Vote block in chat.

## Failure modes

- No diff (branch matches base): say so and exit cleanly.
- Diff too large (>1000 lines): warn, sample 5 most-changed files, suggest splitting
  the PR.
- All findings low-confidence: say so explicitly — don't fabricate severity.

## Telemetry

Logs finding count by severity. Findings older than 90 days are pruned per
`hivestack-config retention_days`.
