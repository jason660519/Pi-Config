# hivestack roadmap

| Milestone | Scope | Acceptance |
|---|---|---|
| **M0** Foundation | repo skeleton, `bin/` helpers, `setup`, auto-update | `./setup` works; `/office-hours` discoverable |
| **M1** Core 5 + 5 | 5 roles (ceo, pm, eng-manager, code-reviewer, qa-lead) + 5 commands (`/office-hours`, `/spec`, `/plan-eng-review`, `/review`, `/qa`) + `swarm-browse` stub | end-to-end run produces artifacts in `~/.hivestack/` |
| **M2.1** ✅ Loop close | + 6 roles (learning-officer, release-manager, cso, architect, devops, oncall-sre) + 3 commands (`/retro`, `/learn`, `/ship`) + `hivestack-team-sync` | `/retro` writes back to brain; `/ship` gate runs the 3-voter rule |
| **M2.2** ✅ Brain + Guard | `swarm-brain` (SQLite, stdlib-only) + `swarm-guard` (11 rule patterns + cost ledger); learnings-{log,search} brain-first with JSONL fallback | brain survives session restart, migrates from JSONL; guard blocks `rm -rf /`, `git push --force main`, `git add .env`; cost ledger tracks $ per session |
| **M2.3** Remaining roles | 12 roles (coo, cfo, ux-researcher, designer, tech-writer, backend-eng, frontend-eng, data-eng, perf-eng, accessibility-lead, privacy-officer, compliance-officer) | every council command has ≥2 voters |
| **M2.4** Remaining tools | `swarm-design`, `swarm-bench`, `swarm-scrape`, `swarm-pdf`, `swarm-bridge` (stub driver only) | each tool has SKILL.md + bin + version output |
| **M2.5** Ship pipeline | `/land-and-deploy`, `/canary`, `/freeze`, `/unfreeze`, team-mode bootstrap, auto-update from git remote | `git clone <repo> && ./.claude/skills/hivestack/setup` produces a working install |
| **M3** Multi-agent | `swarm-bridge` with Claude + Codex drivers, role affinity, cost ceiling, `/pair` | same task runs via Claude and Codex, diffed side-by-side |
| **M4** Self-tuning | telemetry pipeline, `/retro` learnings auto-injected on session start, `/benchmark` leaderboard, `/cost-report` | new sessions auto-receive top learnings |

## v0.1 (M1) cut list — shipped 2026-06-08

- [x] folder layout
- [x] `bin/` helpers (paths, config, slug, update-check, telemetry, repo-mode, session-kind, learnings)
- [x] `roles/_charter.md` + 5 role SKILL.md
- [x] 5 command SKILL.md
- [x] `tools/swarm-browse/` stub (SKILL.md + bin + package.json + cli stub)
- [x] `setup` script (link or copy)

## v0.2 (M2.1) cut list — shipped 2026-06-08

- [x] 6 new roles: `learning-officer`, `release-manager`, `cso`, `architect`, `devops`, `oncall-sre`
- [x] 3 new commands: `/retro`, `/learn`, `/ship`
- [x] `bin/hivestack-team-sync` (source → vendored copy, rsync + WIP guard)
- [x] `_charter.md`: council composition table for `/plan-*-review` and `/ship`

## v0.3 (M2.2) cut list — shipped 2026-06-08

- [x] `tools/swarm-brain/` — SQLite store, `enqueue/query/stats/migrate/version`
- [x] `tools/swarm-guard/` — 11 destructive-cmd rule patterns + `budget` + `cost log/list`
- [x] `bin/hivestack-learnings-log` brain-first (JSONL kept as backup)
- [x] `bin/hivestack-learnings-search` brain-first (JSONL fallback when brain absent/errors)
- [x] `bin/hivestack-cost-log` thin wrapper
- [x] Migration verified: 4 existing JSONL rows ingested with timestamps preserved
- [x] heredoc-stdin pipe bug fixed in learnings-search (env-var pattern, same root cause as M1 hivestack-config fix)
- [ ] (M2.5) pre-tool-use hook calling `swarm-guard check` before Bash runs
- [ ] (M2.5) team-mode bootstrapper
- [ ] (M2.5) auto-update from git remote (per-clone)

## Risks tracked

- Role advice collisions → mitigated by `_charter.md` tie-break path
- Backend API outage → mitigated by local-driver fallback in `swarm-bridge` (M3)
- Disk bloat → retention policy in `hivestack-config` (default 90 days)
- Coexistence with gstack → distinct install path + namespaced skill names
