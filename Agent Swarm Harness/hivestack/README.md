# hivestack

> Turn Claude Code into a virtual engineering team — 23 specialist roles, 8 power tools,
> all slash commands, all Markdown, all free, MIT.

Inspired by [gstack](https://github.com/garrytan/gstack). hivestack is the agent-swarm-first
sibling: same folder-per-skill philosophy, but built around a `swarm-bridge` that routes
work across multiple AI coding backends (Claude, Codex, Gemini, local OSS).

## Status

**v0.7 — 23 roles · 8 tools (7 live + 1 auto-detecting) · 19 commands · M4 telemetry**

- **23 roles** across 6 squads — Executive, Product, Engineering, Quality,
  Security, Ops. Council compositions for `/plan-*-review`, `/ship`,
  `/privacy-audit`, `/compliance-check`, `/benchmark`, `/plan-ceo-review`
  defined in [`roles/_charter.md`](roles/_charter.md).
- **19 commands wired**:
  - Discovery: `/office-hours`, `/spec`
  - Review: `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`,
    `/review`, `/qa`, `/privacy-audit`, `/compliance-check`, `/benchmark`
  - Learning: `/retro`, `/learn`, `/cost-report`
  - Ship: `/ship`, `/pair`, `/land-and-deploy`, `/canary`, `/freeze`, `/unfreeze`
- **8 tools** — status as of v0.7:
  - **Live**: `swarm-brain` (SQLite), `swarm-guard` (PreToolUse hook live),
    `swarm-bridge` (driver loader + real dispatch to claude / codex / mock),
    `swarm-scrape` (stdlib urllib + robots.txt), `swarm-pdf` (md → HTML →
    PDF via Chrome), `swarm-design` (3 Tailwind variants + gallery),
    `swarm-bench` (suite loader + runner via swarm-bridge)
  - **Auto-detecting**: `swarm-browse` (Playwright when installed; stub otherwise)
- **`./setup --team`** installs hivestack + registers the PreToolUse
  hook in the current repo. `rm -rf /` is blocked before Bash runs.
- Cross-session memory persists via SQLite; `/retro` mines it, `/learn`
  reads it, preamble auto-injects same-skill + severity:error lessons.
- M4 telemetry: `hivestack-telemetry-rollup` aggregates daily, `/cost-report`
  rolls the guard ledger by session / day / skill.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what M3 / M4 add.

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

Team-facing usage guide: [`docs/SKILLS_GUIDE.md`](docs/SKILLS_GUIDE.md)

Artifacts land in `~/.hivestack/projects/<repo-slug>/`.

## Layout

```
hivestack/
├── bin/              # shared CLI helpers (paths, config, telemetry, learnings, hook, sync, …)
├── roles/            # 23 specialist persona prompts (_charter.md is the contract)
├── commands/         # 18 slash commands
├── tools/            # 8 power tools (7 with real backends + 1 stub-with-detection)
├── agents/           # swarm-bridge driver YAML (claude.yaml, codex.yaml, mock.yaml)
└── docs/             # ROADMAP, HOOKS, SKILLS_GUIDE
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
