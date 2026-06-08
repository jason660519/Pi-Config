---
name: qa
kind: command
version: 0.1.0
description: QA Lead designs a test matrix and drives a real browser against a URL.
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - AskUserQuestion
triggers:
  - qa this
  - qa the staging
  - smoke test this url
  - verify the deploy
preferred-backends:
  - claude
roles_invoked:
  - qa-lead
tools_invoked:
  - swarm-browse
---

## When to invoke

After implementation and `/review`, before `/ship`. Invoke proactively when the user
deploys to staging or asks "does it actually work in the browser?". Also when the
user types `/qa <url>`.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill qa 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill qa)
```

## Inputs

- `<url>` — the URL to test (staging, local dev server, or production canary).
- (Optional) `--feature <slug>` — restrict to one feature's golden path.

## Steps

1. **Load `roles/qa-lead/SKILL.md`** and adopt the QA Lead persona.
2. **Build the test matrix first** using the template in the role SKILL.md.
   Do not browse until the matrix is written down. Ask the user to confirm scope.
3. **Check `swarm-browse` availability**:
   ```bash
   if [ -x ~/.claude/skills/hivestack/tools/swarm-browse/bin/swarm-browse ]; then
     SWARM_BROWSE=~/.claude/skills/hivestack/tools/swarm-browse/bin/swarm-browse
   else
     SWARM_BROWSE=""
   fi
   ```
4. **Drive the browser** (if `swarm-browse` available):
   - Open the URL, screenshot baseline.
   - Walk the golden path; screenshot at each verifiable state.
   - Walk each edge case; screenshot failure or absence of failure.
   - Save screenshots under `~/.hivestack/projects/<slug>/qa/<feature>-<ts>/`.
   - If `swarm-browse` is the stub (M1), it prints "stub: would navigate to <url>" —
     walk the user through manual steps and ask them to paste screenshot paths.
5. **Write the QA report** to:
   ```
   ~/.hivestack/projects/<slug>/qa/<feature>-<YYYYMMDD-HHMM>.md
   ```
   Use the bug report format from the role SKILL.md for any failures.
6. **Emit the vote block** at the end of the chat response.

## Outputs

- QA report artifact path.
- Screenshot directory path (if browser run completed).
- Vote block in chat.

## Failure modes

- URL unreachable: report it, do not fabricate a pass.
- `swarm-browse` not installed: fall back to matrix-only mode and tell the user
  what to install to unlock automated runs.
- Feature ambiguous (no spec found): ask user to pin which feature this is testing.

## Hand-off

If `pass`: hand off to `/ship`. If `dissent`: list blockers and stop — implementer
fixes, then re-run `/qa`.
