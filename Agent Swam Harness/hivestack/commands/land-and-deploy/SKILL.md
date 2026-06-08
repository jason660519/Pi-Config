---
name: land-and-deploy
kind: command
version: 0.1.0
description: After /ship merges, devops triggers a deploy and oncall-sre watches it.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Write
  - AskUserQuestion
triggers:
  - land and deploy
  - deploy this
  - push to staging
preferred-backends:
  - claude
roles_invoked:
  - devops
  - oncall-sre
  - release-manager
---

## When to invoke

After `/ship` merges to main and you want the change in staging or production.
Invoke when the user says "deploy it" or `/land-and-deploy`. Do NOT invoke
proactively — deployment is always explicit.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill land-and-deploy \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill land-and-deploy)
```

## Inputs

- (Optional) `--env <name>` — target environment. Default: `staging`.
  Production requires explicit `--env production` AND a release note already
  written by `/ship`.
- (Optional) `--strategy <name>` — `rolling` | `blue-green` | `canary`.
  Default: whatever the repo's CI config picks.

## Steps

1. **Refuse early** if:
   - HEAD is not on the merge commit `/ship` just made.
   - There is no release note in `~/.hivestack/projects/<slug>/releases/`
     matching the current commit (no proof gate was passed).
   - `--env production` is set and a `/freeze` lock is active.
2. **Adopt `devops`** from `roles/devops/SKILL.md`.
   - Identify the CI / CD pipeline file in the repo (e.g.,
     `.github/workflows/deploy.yml`).
   - Confirm the rollback path (revert + redeploy, flag kill switch, or
     deploy rollback).
   - Confirm observability: ≥1 metric, ≥1 log field, ≥1 alert with SLO +
     window for the new user-visible path. If absent, dissent — must add
     before deploying.
3. **Trigger the deploy** via the repo's CI:
   - `gh workflow run deploy.yml -f env=<env>` (GitHub Actions), or
   - whatever the repo's `dev.sh` / `deploy.sh` does.
   - Capture the run URL.
4. **Adopt `oncall-sre`** from `roles/oncall-sre/SKILL.md`.
   - Watch the run. If a metric breaches its alert during the watch window
     (default 10 min after deploy completes), open an incident.
5. **Append to the release note**:
   ```markdown
   ## Deploy
   - env: <env>
   - run: <url>
   - completed: <UTC time>
   - watch window: <duration>
   - outcome: clean | alerted (link)
   ```

## Output

- Updated release note artifact path.
- Deploy run URL.
- Watch outcome line.

## Failure modes

- CI workflow file not found: refuse, ask user to identify it.
- `--env production` AND `/freeze` active: refuse with the freeze reason.
- No rollback path: devops dissents; user must supply one or run `/canary`
  with a smaller blast radius.

## Hand-off

If deploy goes clean: recommend `/retro` after the watch window if it was a
meaningful release. If alerts fire: open an incident via `/investigate` — do
NOT auto-rollback unless the repo's runbook says so.
