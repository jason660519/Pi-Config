# hivestack architecture

## Layout

```
hivestack/
├── bin/                      shared helpers (called from every SKILL.md preamble)
├── roles/<slug>/             persona prompts — 23 total at v1.0
│   ├── SKILL.md              YAML frontmatter + system prompt
│   └── playbook.md           optional decision tree
├── commands/<slug>/          slash commands — invoke roles + tools
│   └── SKILL.md
├── tools/<slug>/             power tools — full code, not just markdown
│   ├── SKILL.md
│   ├── bin/<slug>            CLI entrypoint
│   ├── src/                  TypeScript implementation
│   └── package.json
└── docs/                     ROADMAP, ADRs, design notes
```

## Resolution paths

A skill is discovered by Claude Code if any of these are true:

- It sits under `~/.claude/skills/hivestack/<kind>/<slug>/SKILL.md`
- It sits under `<repo>/.claude/skills/hivestack/<kind>/<slug>/SKILL.md` (team mode)
- The user types `/<slug>` and the harness resolves it through CLAUDE.md routing

Each `SKILL.md` carries YAML frontmatter:

```yaml
---
name: <slug>
version: 0.1.0
kind: role | command | tool
description: one-line for routing
allowed-tools: [Bash, Read, Write, ...]
triggers: ["natural phrases"]
preferred-backends: [claude, codex]
---
```

## Storage

```
~/.hivestack/
├── config.json                       per-user settings (telemetry, retention, ...)
├── sessions/<pid>                    active session markers (TTL 120 min)
├── analytics/skill-usage.jsonl       opt-in usage stream
├── learnings/<repo-slug>.jsonl       cross-session lessons
├── projects/<repo-slug>/
│   ├── ideas/<topic>.md              /office-hours output
│   ├── specs/<feature>.md            /spec output
│   ├── plans/<goal>.md               /autoplan output
│   ├── reviews/<branch>-<ts>.md      /review output
│   ├── qa/<feature>-<ts>.md          /qa output
│   ├── security/<branch>-audit.md    /cso output
│   └── decisions/<topic>.md          council vote logs
└── bench/                            /benchmark leaderboards
```

## Multi-agent routing (swarm-bridge, lands in M3)

```
Claude Code (main loop)
        │
        ▼
   swarm-bridge ──► drivers: claude / codex / gemini / ollama
        │
   role-affinity ─► capability-match ─► cost-ceiling ─► concurrency
```

## Charter

See [`roles/_charter.md`](../roles/_charter.md) for tie-break rules and role boundaries.
