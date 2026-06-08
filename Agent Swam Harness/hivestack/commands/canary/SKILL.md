---
name: canary
kind: command
version: 0.1.0
description: devops splits traffic to canary at <pct>%, oncall-sre watches SLOs.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Write
  - AskUserQuestion
triggers:
  - canary
  - canary deploy
  - traffic split
preferred-backends:
  - claude
roles_invoked:
  - devops
  - oncall-sre
---

## When to invoke

When `/land-and-deploy --env production` is too risky for the full
population: a behavioural change, a model swap, a tariff change, anything
where a 1% sample for 30 minutes tells you what you need before the full
rollout.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill canary \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill canary)
```

## Inputs

- `<pct>` — traffic percentage. Must be one of: `1`, `5`, `10`, `25`, `50`.
  Hardcoded set; arbitrary values lead to "oh whatever, 13%" creep.
- (Optional) `--duration <min>` — minimum watch window before promoting.
  Default: 30.
- (Optional) `--auto-promote` — promote to 100% if no SLO breach.
  Default: off (manual promote is safer).

## Steps

1. **Adopt `devops`**.
   - Identify the traffic-split mechanism (feature flag with `% rollout`,
     load-balancer weight, service-mesh rule). If none exists in the repo,
     refuse and instruct user to land one first.
   - Set traffic to `<pct>%` for the canary commit.
   - Capture the change command + revert command (both required).
2. **Adopt `oncall-sre`**.
   - Watch for `<duration>` minutes. Watch: error rate, p95 latency, the
     PRD's primary metric.
   - If any SLO breaches: trigger the revert command captured in step 1.
   - If all SLOs hold for the full duration: surface "promote ready" to
     user via `AskUserQuestion`.
3. **Promote or revert**:
   - Promote: `<pct>` → 100. Confirm via AskUserQuestion unless
     `--auto-promote` and the watch was clean.
   - Revert: traffic back to 0, write incident note (lightweight — full
     postmortem only if SLO actually breached).
4. **Append to release note**:
   ```markdown
   ## Canary
   - pct: <N>%
   - duration: <min>
   - SLOs watched: <list>
   - outcome: promoted | reverted
   - revert command: <captured at start>
   ```

## Output

- Updated release note path.
- Canary outcome (promoted | reverted).

## Failure modes

- No traffic-split mechanism in repo: refuse.
- `<pct>` not in `{1, 5, 10, 25, 50}`: refuse with the allowed set.
- Watch window <30 min for production: warn, require user override.

## Hand-off

If promoted: `/retro` after the next business day. If reverted: `/investigate`.
