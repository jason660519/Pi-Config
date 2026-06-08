---
name: retro
kind: command
version: 0.1.0
description: learning-officer mines recent artifacts for patterns and writes lessons back to brain.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
triggers:
  - retro
  - what did we learn
  - retro the week
  - extract lessons
preferred-backends:
  - claude
roles_invoked:
  - learning-officer
---

## When to invoke

After a milestone, after a SEV incident, or weekly during active development.
Invoke proactively when the user finishes a multi-day push and asks "what did
we learn?" — or when the user types `/retro`.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill retro 2>/dev/null \
  || ./hivestack/bin/hivestack-preamble --skill retro)
```

## Inputs

- (Optional) `--window <days>` — how far back to scan. Default: 14.
- (Optional) `--max <count>` — cap on artifacts read. Default:
  `retro_max_artifacts` from `hivestack-config`, fallback 50.

## Steps

1. **Load `roles/learning-officer/SKILL.md`** and adopt the Chief Learning
   Officer persona.
2. **Resolve paths**:
   ```bash
   eval "$(~/.claude/skills/hivestack/bin/hivestack-paths)"
   eval "$(~/.claude/skills/hivestack/bin/hivestack-slug)"
   WINDOW_DAYS="${WINDOW_DAYS:-14}"
   PROJ="${HIVESTACK_PROJECTS}/${SLUG}"
   ```
3. **Tail recent artifacts**:
   ```bash
   for dir in reviews qa decisions retros security; do
     [ -d "${PROJ}/${dir}" ] && find "${PROJ}/${dir}" -name '*.md' \
       -mtime -"${WINDOW_DAYS}" 2>/dev/null
   done | sort -u | head -"${MAX_ARTIFACTS:-50}"
   ```
4. **For each artifact**: extract intent + outcome + mechanism per the
   learning-officer method.
5. **Cluster by mechanism**, not topic. Drop single-instance clusters unless
   severity = error.
6. **Dedup**: compute `sha1(skill + severity + lowercased note)` and skip if
   the hash is already in `~/.hivestack/learnings/<slug>.jsonl`.
7. **Write the retro** to:
   ```
   ~/.hivestack/projects/<slug>/retros/<YYYYMMDD-HHMM>.md
   ```
8. **Persist lessons**: for each new lesson call
   ```
   hivestack-learnings-log --skill retro --note "<lesson>" --severity <info|warn|error>
   ```
9. **Print** the report path + the top-3 lessons inline.

## Outputs

- Retro artifact path.
- Top 3 lessons in chat.
- Count of new vs re-learned lessons.

## Failure modes

- Empty window: print `no artifacts in window` and exit 0 cleanly.
- All clusters size 1, none severity=error: write the retro with `## What went
  well` only; persist nothing to JSONL.
- JSONL append failure: surface the error, do NOT write a partial retro.

## Idempotency

Re-running within the same window on unchanged artifacts produces an
equivalent retro (same hashes → all duplicates skipped). Per ADR-0001 the dedup
is in-memory hash, not a unique index; two concurrent retros can produce
duplicates — acceptable for v0.1 single-user workstation.

## Hand-off

If the retro surfaces ≥1 severity:error lesson, recommend the user run
`/learn` in their next session to confirm the preamble loads it.
