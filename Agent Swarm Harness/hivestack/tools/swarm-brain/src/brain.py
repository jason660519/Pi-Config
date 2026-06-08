"""swarm-brain — SQLite-backed lesson store.

All persistence goes through one connection, one transaction per call. Dedup
by sha1(skill + severity + lowercased note) enforced at the column UNIQUE
constraint; the application also computes it and ON CONFLICT IGNOREs, so a
race that beats the in-app check still cannot insert a duplicate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"

HIVESTACK_HOME = Path(os.environ.get("HIVESTACK_HOME", os.path.expanduser("~/.hivestack")))
BRAIN_DIR = HIVESTACK_HOME / "brain"
DB_PATH = BRAIN_DIR / "lessons.db"

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS lessons (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  repo      TEXT NOT NULL,
  skill     TEXT NOT NULL,
  severity  TEXT NOT NULL CHECK (severity IN ('info','warn','error')),
  note      TEXT NOT NULL,
  evidence  TEXT,
  hash      TEXT NOT NULL UNIQUE,
  ts        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lessons_repo ON lessons(repo);
CREATE INDEX IF NOT EXISTS idx_lessons_severity ON lessons(severity);
CREATE INDEX IF NOT EXISTS idx_lessons_ts ON lessons(ts);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lesson_hash(skill: str, severity: str, note: str) -> str:
    payload = f"{skill}|{severity}|{note.strip().lower()}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def open_db() -> sqlite3.Connection:
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_V1)
    return conn


def resolve_repo(explicit: str | None) -> str:
    if explicit:
        return explicit
    # Mirror hivestack-slug's behaviour without forking shell.
    try:
        import subprocess

        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if root:
            slug = Path(root).name
            slug = "".join(c for c in slug if c.isalnum() or c in "._-")
            return slug or "unknown"
    except Exception:
        pass
    return "unknown"


def cmd_enqueue(args: argparse.Namespace) -> int:
    if args.severity not in {"info", "warn", "error"}:
        print("severity must be one of: info, warn, error", file=sys.stderr)
        return 1
    if not args.note.strip():
        print("--note cannot be empty", file=sys.stderr)
        return 1
    repo = resolve_repo(args.repo)
    h = lesson_hash(args.skill, args.severity, args.note)
    conn = open_db()
    try:
        with conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO lessons "
                "(repo, skill, severity, note, evidence, hash, ts) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (repo, args.skill, args.severity, args.note,
                 args.evidence, h, utc_now()),
            )
            if cur.rowcount == 0:
                existing = conn.execute(
                    "SELECT id FROM lessons WHERE hash = ?", (h,)
                ).fetchone()
                print(json.dumps({"id": existing["id"], "deduped": True}))
                return 0
            print(json.dumps({"id": cur.lastrowid, "deduped": False}))
            return 0
    finally:
        conn.close()


def cmd_query(args: argparse.Namespace) -> int:
    sql = "SELECT id, ts, repo, skill, severity, note, evidence FROM lessons"
    clauses: list[str] = []
    params: list = []
    if args.repo:
        clauses.append("repo = ?")
        params.append(args.repo)
    if args.severity:
        if args.severity not in {"info", "warn", "error"}:
            print("severity must be one of: info, warn, error", file=sys.stderr)
            return 1
        clauses.append("severity = ?")
        params.append(args.severity)
    if args.like:
        clauses.append("LOWER(note) LIKE ?")
        params.append(f"%{args.like.lower()}%")
    if args.since:
        clauses.append("ts >= ?")
        params.append(args.since)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY ts DESC, id DESC LIMIT ?"
    params.append(args.limit)

    conn = open_db()
    try:
        for row in conn.execute(sql, params):
            print(json.dumps(dict(row)))
    finally:
        conn.close()
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    conn = open_db()
    try:
        params: list = []
        where = ""
        if args.repo:
            where = " WHERE repo = ?"
            params.append(args.repo)
        total = conn.execute(
            f"SELECT COUNT(*) AS n FROM lessons{where}", params
        ).fetchone()["n"]
        by_sev = {
            row["severity"]: row["n"]
            for row in conn.execute(
                f"SELECT severity, COUNT(*) AS n FROM lessons{where} GROUP BY severity",
                params,
            )
        }
        by_skill = {
            row["skill"]: row["n"]
            for row in conn.execute(
                f"SELECT skill, COUNT(*) AS n FROM lessons{where} GROUP BY skill ORDER BY n DESC LIMIT 10",
                params,
            )
        }
        by_repo = (
            {}
            if args.repo
            else {
                row["repo"]: row["n"]
                for row in conn.execute(
                    "SELECT repo, COUNT(*) AS n FROM lessons GROUP BY repo ORDER BY n DESC"
                )
            }
        )
        print(json.dumps({
            "total": total,
            "by_severity": by_sev,
            "top_skills": by_skill,
            "by_repo": by_repo,
        }, indent=2))
    finally:
        conn.close()
    return 0


JSONL_FILENAME_RE = re.compile(r"^(?P<repo>[A-Za-z0-9._-]+)\.jsonl$")


def cmd_migrate(args: argparse.Namespace) -> int:
    src = Path(args.jsonl_dir).expanduser()
    if not src.is_dir():
        print(f"not a directory: {src}", file=sys.stderr)
        return 1
    conn = open_db()
    inserted = 0
    deduped = 0
    skipped = 0
    try:
        with conn:
            for jf in sorted(src.glob("*.jsonl")):
                m = JSONL_FILENAME_RE.match(jf.name)
                if not m:
                    continue
                repo = m.group("repo")
                for line in jf.read_text().splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        skipped += 1
                        continue
                    skill = row.get("skill")
                    severity = row.get("severity", "info")
                    note = row.get("note")
                    ts = row.get("ts") or utc_now()
                    if not skill or not note or severity not in {"info", "warn", "error"}:
                        skipped += 1
                        continue
                    h = lesson_hash(skill, severity, note)
                    cur = conn.execute(
                        "INSERT OR IGNORE INTO lessons "
                        "(repo, skill, severity, note, evidence, hash, ts) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (repo, skill, severity, note,
                         row.get("evidence"), h, ts),
                    )
                    if cur.rowcount == 1:
                        inserted += 1
                    else:
                        deduped += 1
    finally:
        conn.close()
    print(json.dumps({"inserted": inserted, "deduped": deduped, "skipped": skipped}))
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(f"swarm-brain {VERSION}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="swarm-brain")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("enqueue", help="insert one lesson")
    e.add_argument("--skill", required=True)
    e.add_argument("--severity", required=True)
    e.add_argument("--note", required=True)
    e.add_argument("--evidence")
    e.add_argument("--repo")
    e.set_defaults(func=cmd_enqueue)

    q = sub.add_parser("query", help="list lessons")
    q.add_argument("--repo")
    q.add_argument("--severity")
    q.add_argument("--like")
    q.add_argument("--since")
    q.add_argument("--limit", type=int, default=20)
    q.set_defaults(func=cmd_query)

    s = sub.add_parser("stats", help="counts")
    s.add_argument("--repo")
    s.set_defaults(func=cmd_stats)

    m = sub.add_parser("migrate", help="ingest legacy JSONL files")
    m.add_argument("jsonl_dir")
    m.set_defaults(func=cmd_migrate)

    v = sub.add_parser("version", help="print version")
    v.set_defaults(func=cmd_version)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except sqlite3.DatabaseError as e:
        print(f"swarm-brain: storage error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
