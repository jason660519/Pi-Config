---
name: ship
kind: command
version: 0.1.0
description: release-manager runs the three-voter gate (code-reviewer + qa-lead + cso) and ships if pass.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - AskUserQuestion
triggers:
  - ship it
  - ship this
  - ready to ship
  - cut release
preferred-backends:
  - claude
roles_invoked:
  - release-manager
  - code-reviewer
  - qa-lead
  - cso
---

## When to invoke

After `/review` and `/qa` are both green and a security audit exists. Invoke
when the user types `/ship`, "ship it", or "ready to ship". Do NOT invoke
proactively — shipping is always explicit.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill ship 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill ship)
```

## Inputs

- (Optional) `--branch <name>` — branch to ship. Default: current branch.
- (Optional) `--base <ref>` — merge target. Default: `main` (or `master`).
- (Optional) `--no-push` — perform merge locally; skip `git push`.

## Steps

1. **Adopt `release-manager` persona** from `roles/release-manager/SKILL.md`.
   This command is the gate orchestrator, not a coder.
2. **Refuse early** if any of these are true:
   - Current branch == base branch (nothing to ship).
   - There are uncommitted changes (`git status --porcelain` non-empty).
   - **Freeze active** AND PR lacks the allow-label:
     ```bash
     REPO_ROOT="$(git rev-parse --show-toplevel)"
     FREEZE="${REPO_ROOT}/.claude/skills/hivestack/FREEZE"
     if [ -f "${FREEZE}" ]; then
       # parse expires field; if not expired AND PR lacks allow_label → refuse
       python3 - <<'PY'
     import json, os, sys
     from datetime import datetime, timezone
     with open(os.environ["FREEZE"]) as f:
         d = json.load(f)
     exp = datetime.strptime(d["expires"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
     if datetime.now(timezone.utc) < exp:
         # active — caller decides label check via gh pr view
         print(f"FREEZE ACTIVE: {d['reason']} (set by {d.get('set_by','?')}, expires {d['expires']})")
         sys.exit(1)
     PY
     fi
     ```
     If freeze is active, check the PR's labels via `gh pr view --json labels`
     for the `allow_label` from FREEZE (default `hotfix`); proceed only if present.
3. **Collect the three voter artifacts** — most recent for the current
   branch / commit:
   ```bash
   eval "$(~/.claude/skills/hivestack/bin/hivestack-paths)"
   eval "$(~/.claude/skills/hivestack/bin/hivestack-slug)"
   BRANCH="$(git branch --show-current)"
   PROJ="${HIVESTACK_PROJECTS}/${SLUG}"
   REVIEW=$(ls -t "${PROJ}/reviews/${BRANCH}-"*.md 2>/dev/null | head -1)
   QA=$(ls -t "${PROJ}/qa/"*.md 2>/dev/null | head -1)
   SEC=$(ls -t "${PROJ}/security/${BRANCH}-"*.md 2>/dev/null | head -1)
   ```
   For each missing voter, print which `/<cmd>` to run and STOP. Do not invent
   votes.
4. **Apply charter rule**: each voter ≥3 AND no `must_fix` → continue.
   Else: emit blockers + STOP. The release-manager NEVER overrides a voter.
5. **Rollback check**: scan the diff for a flag/migration/rollback signal
   (see `roles/release-manager/SKILL.md` rule 3). If none: ASK the user via
   `AskUserQuestion` for a rollback plan. Record their answer in the release note.
6. **Ask to merge**: `AskUserQuestion` "Confirm merge `<branch>` → `<base>`?"
   Default option is "yes, fast-forward only". User must approve explicitly.
7. **Merge**:
   ```bash
   git checkout "${BASE}" && git pull --ff-only origin "${BASE}" \
     && git merge --ff-only "${BRANCH}"
   ```
   If FF impossible, STOP and report — do NOT auto-rebase or merge-commit.
8. **Push** (unless `--no-push`):
   ```bash
   git push origin "${BASE}"
   ```
9. **Delete branch** only after the user confirms via `AskUserQuestion`. Local
   AND remote deletion are two separate confirmations; default option is "keep both".
10. **Write the release note** to:
    ```
    ~/.hivestack/projects/<slug>/releases/<branch>-<YYYYMMDD-HHMM>.md
    ```
11. **Emit the gate-result block** in chat (see release-manager SKILL.md).

## Outputs

- Release note artifact path.
- Gate-result block.
- Merge commit SHA (or "fast-forward to <sha>").
- If PR existed: print PR URL and note GitHub auto-closes it on push.

## Failure modes

- Any voter missing or stale (>24h): STOP, name the missing/stale voter.
- Any voter `dissent`: STOP, list `must_fix` items.
- No rollback path AND user can't supply one: STOP — refuse to ship.
- `git merge --ff-only` fails: STOP, recommend rebase by hand (don't auto-rebase).

## Hard rules

- NEVER force-push.
- NEVER `git reset --hard` shared branches.
- NEVER skip a voter's `must_fix` to "unblock" — escalate to user instead.
- NEVER `git push` without an `AskUserQuestion` confirmation, even in
  team-mode auto-update contexts.

## Hand-off

After successful ship: recommend `/retro` to mine this work for lessons.
