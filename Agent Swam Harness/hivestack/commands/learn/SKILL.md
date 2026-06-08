---
name: learn
kind: command
version: 0.1.0
description: Query the brain for relevant past lessons and render them inline.
allowed-tools:
  - Bash
  - Read
  - Grep
triggers:
  - what do we know about
  - any lessons on
  - learn
  - check brain
preferred-backends:
  - claude
roles_invoked: []
---

## When to invoke

When the user asks "have we seen this before?", "any lessons on X?", or starts
a task in an area we've worked on. Invoke proactively at the start of a new
session if the previous session ended with a `/retro` that produced
severity:error lessons.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill learn 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill learn)
```

## Inputs

- (Optional) `<query>` — substring to filter lessons by. Default: print last N.
- (Optional) `--limit <n>` — how many to render. Default: 10.
- (Optional) `--severity <info|warn|error>` — filter.

## Steps

1. **Resolve paths**:
   ```bash
   eval "$(~/.claude/skills/hivestack/bin/hivestack-paths)"
   eval "$(~/.claude/skills/hivestack/bin/hivestack-slug)"
   LF="${HIVESTACK_LEARNINGS}/${SLUG}.jsonl"
   ```
2. **Empty case**: if `${LF}` doesn't exist OR is empty, print
   `no lessons logged for ${SLUG} yet — run /retro after some work` and exit 0.
3. **Filter**: when a `<query>` is supplied, restrict lines whose `note` field
   contains the substring (case-insensitive). When `--severity` is supplied,
   restrict to matching rows.
4. **Render** the matched rows newest-first:
   ```
   • [<skill>/<severity>] <note>
     evidence: <citation> (optional)
   ```
   Use [`bin/hivestack-learnings-search`](../../bin/hivestack-learnings-search)
   for the no-filter case; for filtered cases inline the same render.
5. **Suggest**: if the query is non-empty and zero matches, print
   `no prior lessons on "<query>"` and one line of why-this-matters.

## Outputs

- Inline list in chat.
- No artifact written — `/learn` is read-only.

## Failure modes

- Malformed JSONL row: skip it, do NOT abort; surface a count of skipped rows
  at the end if >0.
- Brain backend later (M2.2) returns transport error: fall back to the local
  JSONL automatically — print one warning then proceed.

## Hand-off

If matches found and the user is about to do work in an area the lessons
warn against, suggest the relevant gate command (`/cso`, `/review`) instead
of going straight to implementation.
