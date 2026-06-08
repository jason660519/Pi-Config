---
name: unfreeze
kind: command
version: 0.1.0
description: Lift an active /freeze. Auditable — appends to unfreeze-log.
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - unfreeze
  - lift freeze
  - unlock the repo
preferred-backends:
  - claude
roles_invoked:
  - release-manager
---

## When to invoke

When a `/freeze` is active and the reason no longer applies (release window
done, incident resolved, quiet period over). Invoke explicitly — never
auto-lift, even on the documented `expires` timestamp (let `/ship` notice
the expiry and proceed silently).

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill unfreeze \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill unfreeze)
```

## Inputs

- `--reason "<text>"` — required. Why we're lifting. Appended to audit log.

## Steps

1. **Refuse if no FREEZE file exists** at
   `<repo>/.claude/skills/hivestack/FREEZE`. Print "no freeze active" and exit 0.
2. **Read the existing lockfile**. Print its `reason`, `set_at`, `expires`,
   `set_by` so the user sees what's being lifted.
3. **Confirm via `AskUserQuestion`**: "Lift freeze set <when> by <who>?
   Reason was: <reason>." Default option: "no, keep frozen".
4. **Append to audit log**:
   ```
   <repo>/.claude/skills/hivestack/UNFREEZE-LOG
   ```
   One JSON-line per lift:
   ```json
   {"ts":"<UTC>","lifted_by":"<email>","prior_reason":"<text>","lift_reason":"<text>"}
   ```
5. **Delete the FREEZE file**.
6. **Remind the user to commit** both the FREEZE deletion and the
   UNFREEZE-LOG append — we do NOT auto-commit.

## Output

- Confirmation that freeze is lifted.
- Path to the appended audit log line.
- Reminder to `git commit`.

## Failure modes

- FREEZE file unreadable / malformed: refuse, recommend manual inspection.
- User answers "no, keep frozen": exit 0, no changes.

## Hard rules

- Never lift a freeze without an AskUserQuestion confirmation, even when
  `--auto-unfreeze` is somehow set (there is no such flag — refuse to add one).
- Every lift produces an audit log line. The log is the only signal future
  retros have that a freeze happened and was actively lifted (vs expired
  silently).
