"""swarm-guard — destructive-command static checker + cost ledger."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"

HIVESTACK_HOME = Path(os.environ.get("HIVESTACK_HOME", os.path.expanduser("~/.hivestack")))
GUARD_DIR = HIVESTACK_HOME / "guard"
BUDGET_PATH = GUARD_DIR / "budget.json"
LEDGER_PATH = GUARD_DIR / "cost-ledger.jsonl"

SEVERITIES = {"ok": 0, "warn": 1, "block": 2}


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: re.Pattern
    severity: str
    reason: str


# IMPORTANT: keep these patterns narrow. False positives erode trust faster
# than false negatives, since users start passing --bypass everywhere.
RULES: list[Rule] = [
    Rule(
        "rm-root",
        re.compile(r"\brm\s+(-[rRf]+\s+)+(/|\$HOME)(\s|$|\")", re.IGNORECASE),
        "block",
        "filesystem wipe (rm -rf /, rm -rf $HOME)",
    ),
    Rule(
        "rm-unset-var",
        re.compile(r"\brm\s+-[rRf]+\s+[\"']?\$[A-Z_][A-Z0-9_]*[\"']?/", re.IGNORECASE),
        "block",
        "rm -rf $VAR/ — unset var expands to '/'",
    ),
    Rule(
        "rm-recursive-dot",
        re.compile(r"\brm\s+-[rRf]+\s+\.(\s|$)", re.IGNORECASE),
        "warn",
        "rm -rf . — likely meant a subpath",
    ),
    Rule(
        "git-force-main",
        re.compile(r"\bgit\s+push\s+.*--force(-with-lease)?\b.*\b(main|master|release/[\w.-]+)\b", re.IGNORECASE),
        "block",
        "force push to mainline branch",
    ),
    Rule(
        "git-reset-hard-shared",
        re.compile(r"\bgit\s+reset\s+--hard\s+(origin/)?(main|master)\b", re.IGNORECASE),
        "block",
        "git reset --hard on a shared branch rewrites history",
    ),
    Rule(
        "chmod-777-root",
        re.compile(r"\bchmod\s+(-R\s+)?777\s+(/|\$HOME|~)(\s|$|\")", re.IGNORECASE),
        "block",
        "chmod 777 on /, $HOME, or ~",
    ),
    Rule(
        "curl-pipe-bash",
        re.compile(r"\bcurl\s+[^|]+\|\s*(sudo\s+)?(ba)?sh\b", re.IGNORECASE),
        "warn",
        "curl … | sh runs remote code",
    ),
    Rule(
        "secrets-staged",
        re.compile(r"\bgit\s+add\s+.*(\.env(\.[a-z0-9_-]+)?\b|\.pem\b|id_rsa\b|credentials\.json\b)", re.IGNORECASE),
        "block",
        "likely-secret file staged for commit",
    ),
    Rule(
        "dd-of-dev",
        re.compile(r"\bdd\s+[^\n]*of=/dev/(sd|nvme|disk|hd)", re.IGNORECASE),
        "block",
        "dd of=/dev/sdX overwrites a block device",
    ),
    Rule(
        "git-config-global",
        re.compile(r"\bgit\s+config\s+--global\b", re.IGNORECASE),
        "warn",
        "mutating user-wide git config",
    ),
    Rule(
        "npm-i-g-curl",
        re.compile(r"\bnpm\s+(i|install)\s+-g\s+https?://", re.IGNORECASE),
        "warn",
        "npm global install from a URL",
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_check(args: argparse.Namespace) -> int:
    cmd = args.command
    findings: list[Rule] = []
    for rule in RULES:
        if rule.pattern.search(cmd):
            findings.append(rule)
    if not findings:
        return 0
    findings.sort(key=lambda r: SEVERITIES[r.severity], reverse=True)
    for r in findings:
        print(f"[{r.severity}] {r.id}: {r.reason}", file=sys.stderr)
    return SEVERITIES[findings[0].severity]


def _load_budget() -> dict:
    if not BUDGET_PATH.exists():
        return {"budget_usd": None, "session_id": None}
    try:
        return json.loads(BUDGET_PATH.read_text())
    except Exception:
        return {"budget_usd": None, "session_id": None}


def _save_budget(d: dict) -> None:
    GUARD_DIR.mkdir(parents=True, exist_ok=True)
    BUDGET_PATH.write_text(json.dumps(d, indent=2))


def _current_session() -> str:
    return f"{os.getppid()}-{int(time.time())}"


def cmd_budget_set(args: argparse.Namespace) -> int:
    try:
        amount = float(args.usd)
    except ValueError:
        print("usd must be a number", file=sys.stderr)
        return 1
    if amount < 0:
        print("budget must be non-negative", file=sys.stderr)
        return 1
    state = {"budget_usd": amount, "session_id": _current_session(),
             "set_at": utc_now()}
    _save_budget(state)
    print(json.dumps(state))
    return 0


def cmd_budget_status(_: argparse.Namespace) -> int:
    state = _load_budget()
    spent = 0.0
    n = 0
    if state.get("session_id") and LEDGER_PATH.exists():
        for line in LEDGER_PATH.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("session_id") == state["session_id"]:
                spent += float(row.get("usd", 0))
                n += 1
    budget = state.get("budget_usd")
    remaining = None if budget is None else max(0.0, budget - spent)
    print(json.dumps({
        "budget_usd": budget,
        "session_id": state.get("session_id"),
        "spent": round(spent, 4),
        "entries": n,
        "remaining": None if remaining is None else round(remaining, 4),
        "over": False if budget is None else spent > budget,
    }, indent=2))
    return 0


def cmd_cost_log(args: argparse.Namespace) -> int:
    try:
        usd = float(args.usd)
    except ValueError:
        print("usd must be a number", file=sys.stderr)
        return 1
    state = _load_budget()
    session_id = state.get("session_id") or _current_session()
    GUARD_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": utc_now(),
        "session_id": session_id,
        "usd": usd,
        "description": args.description,
    }
    with LEDGER_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps(entry))
    return 0


def cmd_cost_list(args: argparse.Namespace) -> int:
    if not LEDGER_PATH.exists():
        return 0
    lines = LEDGER_PATH.read_text().splitlines()
    if args.since:
        lines = [ln for ln in lines if (json.loads(ln).get("ts") or "") >= args.since]
    lines = lines[-args.limit:]
    for ln in lines:
        print(ln)
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(f"swarm-guard {VERSION}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="swarm-guard")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="static-check a command string")
    c.add_argument("command")
    c.set_defaults(func=cmd_check)

    b = sub.add_parser("budget", help="session cost budget")
    bs = b.add_subparsers(dest="bcmd", required=True)
    b_set = bs.add_parser("set")
    b_set.add_argument("usd")
    b_set.set_defaults(func=cmd_budget_set)
    b_stat = bs.add_parser("status")
    b_stat.set_defaults(func=cmd_budget_status)

    cost = sub.add_parser("cost", help="append-only cost ledger")
    cs = cost.add_subparsers(dest="ccmd", required=True)
    c_log = cs.add_parser("log")
    c_log.add_argument("usd")
    c_log.add_argument("description")
    c_log.set_defaults(func=cmd_cost_log)
    c_list = cs.add_parser("list")
    c_list.add_argument("--limit", type=int, default=20)
    c_list.add_argument("--since")
    c_list.set_defaults(func=cmd_cost_list)

    v = sub.add_parser("version", help="print version")
    v.set_defaults(func=cmd_version)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
