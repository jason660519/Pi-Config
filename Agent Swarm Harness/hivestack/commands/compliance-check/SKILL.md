---
name: compliance-check
kind: command
version: 0.1.0
description: compliance-officer scans the diff for license, SOC2, vendor-TOS issues.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
triggers:
  - compliance check
  - license audit
  - soc2 review
preferred-backends:
  - claude
roles_invoked:
  - compliance-officer
---

## When to invoke

Whenever a PR adds a new dependency (any package manifest changed), touches
authn/authz, audit logging, or calls a new third-party API. Always invoke
before shipping a release that will be claimed against SOC2 / ISO 27001
controls.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill compliance-check \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill compliance-check)
```

## Inputs

- (Optional) `--base <ref>` — diff base. Default: `main` / `master`.

## Steps

1. **Adopt `compliance-officer`** from `roles/compliance-officer/SKILL.md`.
2. **Detect manifest changes**:
   ```bash
   git diff --name-only "${BASE}"...HEAD | grep -E '(pyproject\.toml|package\.json|Cargo\.toml|go\.mod|Gemfile)'
   ```
   For each, list added / removed deps with their licenses (look up from
   package registry metadata when available).
3. **SOC2 quick-map**: identify which Trust Service Criteria touch the
   changed code (CC6.X for access, CC7.X for monitoring, CC8.X for change
   management).
4. **Vendor TOS scan**: any new third-party API call → check the TOS for
   prohibited categories. If unknown, surface as `should_consider` (NOT
   `must_fix` — guessing wrong about TOS is worse than asking).
5. **Write** the report to
   `~/.hivestack/projects/<slug>/compliance/<branch>-<YYYYMMDD-HHMM>.md`.
6. **Emit the vote block**.

## Output

- Compliance report artifact path.
- Vote block.

## Failure modes

- Manifest parsing fails: surface the parse error, do NOT silently pass.
- Network unavailable for license lookup: warn, mark each new dep as
  `unverified`, dissent.

## Hand-off

If `pass`: continue to `/ship`. If `dissent`: list blockers (typically:
GPL/AGPL in closed-source product, missing SOC2 audit trail, prohibited
vendor TOS use).
