---
name: swarm-guard
kind: tool
version: 0.1.0
description: Block destructive commands and enforce a session cost ceiling. (hivestack)
allowed-tools:
  - Bash
  - Read
triggers:
  - is this safe to run
  - check this command
  - budget status
preferred-backends:
  - claude
---

## What it is

A small static analyzer + ledger. Two jobs:

1. **`check <command>`** — pattern-match against known destructive shapes
   (`rm -rf /`, `git push --force` to main, `git reset --hard` of a shared
   branch, `chmod -R 777 /`, `curl … | bash`, hardcoded secrets in a `git add`
   target, etc.). Exit code says what to do: 0 ok, 1 warn, 2 block. The
   reason is on stderr.

2. **`budget` / `cost log`** — append-only ledger of estimated $ spent per
   session. `budget set <usd>` caps the session; `cost log <usd> <desc>`
   appends; `budget status` reports remaining. When remaining hits 0, the
   intent is for callers (or `swarm-bridge` in M3) to refuse further LLM
   calls. v0.1 only reports — enforcement is M3's swarm-bridge job.

This is **static**, not a sandbox: it reads strings, it does not run the
command, it cannot block what it doesn't see. It exists to catch the obvious
foot-guns before they get typed into Bash.

## CLI

```bash
swarm-guard check '<command-string>'
# rc=0 ok / rc=1 warn / rc=2 block; reason on stderr
# Multiple findings: stderr lists each on its own line, exit = highest severity

swarm-guard budget set <usd>
swarm-guard budget status                       # JSON: {budget, spent, remaining, sessions}
swarm-guard cost log <usd> "<description>"
swarm-guard cost list [--limit <n>] [--since <iso-date>]

swarm-guard version
```

## Rule set (v0.1)

| ID | Pattern (regex, case-insensitive on the command) | Severity | Reason |
|---|---|---|---|
| `rm-root` | `rm\s+(-[rRf]+\s+)+(/|\$HOME)(\s\|$)` | block | filesystem wipe |
| `rm-unset-var` | `rm\s+-rf\s+["']?\$[A-Z_]+["']?/` | block | unset var expands to '/' |
| `rm-recursive-dot` | `rm\s+-rf\s+\.(\s|$)` | warn | likely meant a subpath |
| `git-force-main` | `git\s+push\s+.*--force.*\b(main\|master)\b` | block | force push to mainline |
| `git-reset-hard-shared` | `git\s+reset\s+--hard\s+(origin/)?(main\|master)\b` | block | rewriting shared history |
| `chmod-777-root` | `chmod\s+(-R\s+)?777\s+(/|\$HOME|\~)\b` | block | mode 777 on root/home |
| `curl-pipe-bash` | `curl\s+[^\|]+\|\s*(sudo\s+)?(ba)?sh\b` | warn | running remote code |
| `secrets-staged` | `git\s+add\s+.*(\.env(\.[a-z]+)?\b\|\.pem\b\|id_rsa\b\|credentials\.json\b)` | block | likely-secret file staged |
| `dd-of-dev` | `dd\s+.*of=/dev/(sd|nvme|disk)` | block | raw write to a block device |
| `git-config-global` | `git\s+config\s+--global\b` | warn | mutating user-wide git config |
| `npm-i-g-curl` | `npm\s+(i\|install)\s+-g\s+http` | warn | global install from URL |

Order matters: highest severity wins. Patterns are intentionally narrow — a
false positive on `rm -rf node_modules` should NOT trigger `rm-root`.

## Storage

```
~/.hivestack/guard/
├── budget.json          {"budget_usd": 5.00, "session_id": "<pid>-<ts>"}
└── cost-ledger.jsonl    append-only: {ts, session_id, usd, description}
```

`budget set` rotates the session id; `cost log` writes against the current
session. `budget status` sums the current session only.

## Roadmap

- M2.2 (this) — static check + cost ledger
- M2.5 — wire `check` into Claude Code pre-tool-use hook so blocks happen
         before Bash actually runs
- M3 — `swarm-bridge` consults `budget remaining` before every LLM call
- M3 — allowlist mode (additive rules from a YAML file)
