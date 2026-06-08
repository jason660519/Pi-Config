---
name: swarm-brain
kind: tool
version: 0.1.0
description: SQLite-backed lesson store for cross-session memory. (hivestack)
allowed-tools:
  - Bash
  - Read
triggers:
  - check brain
  - brain stats
  - what's in brain
preferred-backends:
  - claude
---

## What it is

Replaces the v0.1 flat JSONL learning store with a structured SQLite database.
Same hash dedup (`sha1(skill+severity+lowercased note)`), better query, atomic
writes, indexes on `repo` and `severity`. Pure Python stdlib — no extra deps.

When brain is installed, `hivestack-learnings-log` and `hivestack-learnings-search`
prefer it; if the brain CLI is missing or errors, both fall back to the JSONL
path transparently. JSONL files are NEVER deleted by brain — they remain as the
source-of-truth backup until M3 promotes brain to canonical.

## Storage

```
~/.hivestack/brain/lessons.db          SQLite database
~/.hivestack/brain/schema-v1.sql       schema, applied on first init
~/.hivestack/learnings/<slug>.jsonl    fallback + backup (unchanged)
```

Schema v1:

```sql
CREATE TABLE lessons (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  repo      TEXT NOT NULL,
  skill     TEXT NOT NULL,
  severity  TEXT NOT NULL CHECK (severity IN ('info','warn','error')),
  note      TEXT NOT NULL,
  evidence  TEXT,                          -- e.g. "src/foo.py:42"
  hash      TEXT NOT NULL UNIQUE,          -- dedup key
  ts        TEXT NOT NULL                  -- ISO 8601 UTC
);
CREATE INDEX idx_lessons_repo ON lessons(repo);
CREATE INDEX idx_lessons_severity ON lessons(severity);
CREATE INDEX idx_lessons_ts ON lessons(ts);
```

## CLI

```bash
swarm-brain enqueue --skill <name> --severity <info|warn|error> \
                    --note "<text>" [--evidence "<file:line>"] \
                    [--repo <slug>]
# Returns: {"id": <n>, "deduped": <bool>}
# If deduped == true, no row was written; existing id is returned.

swarm-brain query   [--repo <slug>] [--severity <s>] [--like "<substr>"] \
                    [--since <iso-date>] [--limit <n>]
# Returns: JSONL on stdout, newest first.

swarm-brain stats   [--repo <slug>]
# Returns: counts per repo / severity / skill.

swarm-brain migrate <jsonl-dir>
# Ingest existing JSONL files into the DB. Idempotent (dedup by hash).

swarm-brain version
```

Exit codes: 0 ok, 1 usage error, 2 storage error.

## Why SQLite

- stdlib in Python (no install step)
- atomic writes via single-row INSERT
- `UNIQUE(hash)` does the dedup work the v0.1 in-memory hash was emulating
- `WHERE repo = ? AND severity = ?` is the query the preamble actually runs
- backups: `sqlite3 lessons.db .dump > backup.sql` — plain SQL, portable

## Roadmap

- M2.2 (this) — SQLite-only, single-host
- M2.5 — optional Postgres/Supabase backend for team-mode shared brain
- M3 — promote to canonical (JSONL becomes export format only)
- M4 — semantic search via embeddings sidecar
