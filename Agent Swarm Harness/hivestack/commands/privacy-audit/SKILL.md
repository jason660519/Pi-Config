---
name: privacy-audit
kind: command
version: 0.1.0
description: privacy-officer audits the diff for PII, retention, deletion paths.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
triggers:
  - privacy audit
  - pii check
  - gdpr review
preferred-backends:
  - claude
roles_invoked:
  - privacy-officer
---

## When to invoke

Whenever a PR introduces a new persisted column, a new log statement, an LLM
prompt template that may include user data, or any change to retention /
deletion code. Always invoke before `/ship` if `privacy_required: true` is
set in the PRD's rollout section.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill privacy-audit \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill privacy-audit)
```

## Inputs

- (Optional) `--base <ref>` — diff base. Default: `main` / `master`.

## Steps

1. **Adopt `privacy-officer`** from `roles/privacy-officer/SKILL.md`.
2. **Gather diff**:
   ```bash
   BASE="${BASE:-$(git rev-parse --verify main 2>/dev/null || git rev-parse --verify master)}"
   git diff "${BASE}"...HEAD
   ```
3. **Run the 4-step method** from the role SKILL.md: PII grep, write/read
   tracing, log/prompt scan, deletion path trace.
4. **For each finding** produce the YAML block per the role's voting
   protocol.
5. **Write** the report to
   `~/.hivestack/projects/<slug>/privacy/<branch>-<YYYYMMDD-HHMM>.md`.
6. **Emit the vote block**.

## Output

- Privacy report artifact path.
- Vote block.

## Hand-off

If `pass`: continue to `/cso` and `/ship`. If `dissent`: stop. Implementer
fixes redaction / retention, re-run `/privacy-audit`.
