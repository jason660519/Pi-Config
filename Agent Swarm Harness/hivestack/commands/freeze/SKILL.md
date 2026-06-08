---
name: freeze
kind: command
version: 0.1.0
description: Lock the repo against /ship — hotfix label required to bypass.
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - freeze
  - merge freeze
  - lock the repo
preferred-backends:
  - claude
roles_invoked:
  - release-manager
---

## When to invoke

Before a release window when no merges to main should happen. Before / during
a SEV-1/2 incident when the surface is fragile. Before a tariff change /
quiet-period window. Invoke explicitly when the user says "freeze".

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill freeze \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill freeze)
```

## Inputs

- `--reason "<text>"` — required. Why the freeze; goes into the lockfile so
  future sessions know.
- `--expires <ISO-date>` — required. When the freeze auto-lifts.
- (Optional) `--allow-label <name>` — PR label that bypasses freeze.
  Default: `hotfix`.

## Steps

1. **Refuse if a freeze is already active** (lockfile exists at
   `<repo>/.claude/skills/hivestack/FREEZE`). Print the existing reason +
   expiry, recommend `/unfreeze` if you really want to override.
2. **Write the lockfile**:
   ```
   <repo>/.claude/skills/hivestack/FREEZE
   ```
   Content (one JSON object):
   ```json
   {
     "reason": "<text>",
     "set_at": "<UTC ISO>",
     "expires": "<UTC ISO>",
     "allow_label": "hotfix",
     "set_by": "<git config user.email or 'unknown'>"
   }
   ```
3. **Update `_charter.md` runtime view**: `/ship` checks for this lockfile
   and refuses unless the PR carries the allow-label.
4. **Print** the lockfile path and expiry.

## Output

- Lockfile path.
- Expiry timestamp.
- One-line "freeze active until <expiry>; bypass with label `<name>`".

## What `/ship` does when freeze is active

The release-manager preamble re-reads `FREEZE` on every `/ship` invocation.
If the file exists AND has not expired AND the current branch's PR does not
carry the allow-label, `/ship` refuses with the freeze reason and a pointer
to `/unfreeze`.

## Hard rules

- NEVER edit `FREEZE` to bypass; use `/unfreeze` (which is auditable).
- The lockfile is **committed** to the repo by convention so every
  contributor's Claude Code session sees it. The user must `git commit`
  after this command — we do NOT auto-commit (CLAUDE.md rule).
