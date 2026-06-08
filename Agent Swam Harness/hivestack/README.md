# hivestack

> Turn Claude Code into a virtual engineering team — 23 specialist roles, 8 power tools,
> all slash commands, all Markdown, all free, MIT.

Inspired by [gstack](https://github.com/garrytan/gstack). hivestack is the agent-swarm-first
sibling: same folder-per-skill philosophy, but built around a `swarm-bridge` that routes
work across multiple AI coding backends (Claude, Codex, Gemini, local OSS).

## Status

**v0.1 — M0 + M1 foundations**

- 5 core roles wired: `ceo`, `pm`, `eng-manager`, `code-reviewer`, `qa-lead`
- 5 core commands: `/office-hours`, `/spec`, `/plan-eng-review`, `/review`, `/qa`
- 1 power tool stub: `swarm-browse`
- Shared `bin/hivestack-*` helpers
- Self-install via `./setup`

The remaining 18 roles, 7 tools, and 25+ commands are scaffolded as milestones in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## Install

```bash
git clone --single-branch --depth 1 <this-repo> ~/.claude/skills/hivestack
cd ~/.claude/skills/hivestack
./setup
```

Or from inside this repo:

```bash
./setup --link    # symlinks ~/.claude/skills/hivestack -> this dir
```

## Quick start

```
/office-hours              # CEO grills your idea
/spec <feature>            # PM writes a PRD
/plan-eng-review           # Eng Manager + Architect sign off architecture
/review                    # Code Reviewer scans the current diff
/qa <url>                  # QA Lead drives a real browser
```

Artifacts land in `~/.hivestack/projects/<repo-slug>/`.

## Layout

```
hivestack/
├── bin/              # shared CLI helpers (paths, config, telemetry, learnings)
├── roles/            # 23 specialist persona prompts (5 wired in v0.1)
├── commands/         # slash commands (5 wired in v0.1)
├── tools/            # power tools with native code (swarm-browse stub in v0.1)
└── docs/             # architecture, roadmap, decisions
```

## Design philosophy

1. **Markdown is the contract.** Every role, command, and tool is a folder with `SKILL.md`.
   Claude reads it on invocation. Code is only added where a script alone won't do.
2. **Multi-agent is first-class.** `swarm-bridge` routes tasks to whichever backend fits —
   role affinity, capability match, and cost ceiling decide. Falls back to local OSS.
3. **Telemetry feeds learnings.** Every skill run logs to `~/.hivestack/`. `/retro` and
   `/learn` mine that for failure patterns and inject them into future sessions.
4. **Gates over guidance.** `/ship` won't proceed unless `code-reviewer` + `qa-lead` + `cso`
   sign off. No "trust me bro" merges.

## License

MIT. Fork it. Make it yours.
