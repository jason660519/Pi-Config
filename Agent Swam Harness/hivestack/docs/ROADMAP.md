# hivestack roadmap

| Milestone | Scope | Acceptance |
|---|---|---|
| **M0** Foundation | repo skeleton, `bin/` helpers, `setup`, auto-update | `./setup` works; `/office-hours` discoverable |
| **M1** Core 5 + 5 | 5 roles (ceo, pm, eng-manager, code-reviewer, qa-lead) + 5 commands (`/office-hours`, `/spec`, `/plan-eng-review`, `/review`, `/qa`) + `swarm-browse` stub | end-to-end run produces artifacts in `~/.hivestack/` |
| **M2.1** ✅ Loop close | + 6 roles (learning-officer, release-manager, cso, architect, devops, oncall-sre) + 3 commands (`/retro`, `/learn`, `/ship`) + `hivestack-team-sync` | `/retro` writes back to brain; `/ship` gate runs the 3-voter rule |
| **M2.2** ✅ Brain + Guard | `swarm-brain` (SQLite, stdlib-only) + `swarm-guard` (11 rule patterns + cost ledger); learnings-{log,search} brain-first with JSONL fallback | brain survives session restart, migrates from JSONL; guard blocks `rm -rf /`, `git push --force main`, `git add .env`; cost ledger tracks $ per session |
| **M2.3** ✅ Remaining roles | 12 roles (coo, cfo, ux-researcher, designer, tech-writer, backend-eng, frontend-eng, data-eng, perf-eng, accessibility-lead, privacy-officer, compliance-officer) | every council command in the charter has ≥2 voters wired |
| **M2.4** ✅ Remaining tools | `swarm-design`, `swarm-bench`, `swarm-scrape`, `swarm-pdf`, `swarm-bridge` (stubs) | each tool has SKILL.md + bin + version output + unknown-cmd rc=2 |
| **M2.5a** ✅ Hooks + team mode | `bin/hivestack-pretool-hook` (Claude Code PreToolUse), `bin/hivestack-team-init` (writes `.claude/settings.json`), `./setup --team`, `docs/HOOKS.md` | `rm -rf /` is blocked **before** Bash runs; team-init is idempotent and merges into existing settings.json |
| **M2.5b** ✅ Ship pipeline | `/land-and-deploy`, `/canary`, `/freeze`, `/unfreeze`, `/plan-design-review`, `/privacy-audit`, `/compliance-check`, `/benchmark`, `bin/hivestack-auto-update` | every council role has a wired command; freeze blocks `/ship`; auto-update fast-forwards vendored copy once/hour |
| **M3** ✅ Real backends | `swarm-bridge` (claude+codex+mock drivers, real subprocess dispatch), `swarm-scrape` (urllib+robots), `swarm-pdf` (Chrome print-to-PDF), `swarm-design` (3 Tailwind templates + gallery), `swarm-bench` (suite loader+runner), `swarm-browse` (Playwright detection), `/pair` | same task runs via two backends, diff in `~/.hivestack/projects/<slug>/pair/`; bridge real-dispatches to `claude` CLI; PDF and HTML render end-to-end |
| **M4** ✅ Self-tuning | `bin/hivestack-telemetry-rollup` (daily aggregate), `/cost-report` (by session/day/skill), smart learning inject (same-skill + severity:error filter on preamble) | preamble auto-injects same-skill lessons; cost-ledger rolls up by skill (convention: `<skill>: <detail>` description); telemetry rollup writes daily JSON |

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

## v0.7 (M3 + M4) cut list — shipped 2026-06-08

Six stubs → real, two new commands, M4 self-tuning shipped together.

### Tools upgraded stub → live
- [x] `swarm-bridge` v0.2: driver loader, YAML schema, `agents/{claude,codex,mock}.yaml`, real `route/run/list-backends/health/cost-quote`; verified end-to-end dispatch to `claude` CLI returning a real Opus response
- [x] `swarm-scrape` v0.2: `fetch/crawl/robots` using stdlib urllib; honours robots.txt + per-domain rate limit (2s); `--insecure` flag for macOS Python SSL workaround
- [x] `swarm-pdf` v0.2: markdown → HTML → PDF via Chrome/wkhtmltopdf shell-out; verified ~190KB PDF from a real spec artifact
- [x] `swarm-design` v0.2: `new/variants/gallery/list-sessions`; three deliberately-distinct Tailwind templates (minimal / dense / dark-prosumer); each variant includes empty/loading/error states
- [x] `swarm-bench` v0.2: suite YAML schema + runner that dispatches via swarm-bridge; writes per-run `summary.json` with `n/ok/p50_ms/max_ms` per backend
- [x] `swarm-browse` v0.2: Playwright auto-detection; real `open/wait/close` when installed, falls back to stub mode otherwise

### New commands
- [x] `/pair "<prompt>" [--a <backend>] [--b <backend>]` — dual-backend dispatch via swarm-bridge; side-by-side render; user picks winner via AskUserQuestion
- [x] `/plan-ceo-review` — ceo + cfo two-voter council (was listed in charter but never had a SKILL.md; fixed)
- [x] `/cost-report [--since <date>] [--by session|day|skill]` — cfo rolls up `~/.hivestack/guard/cost-ledger.jsonl`

### M4 self-tuning
- [x] `bin/hivestack-telemetry-rollup` — daily aggregate of all `analytics/*.jsonl` streams (skills × outcomes × tools × repos)
- [x] `bin/hivestack-cost-report` — by session / day / skill rolls; current budget visible
- [x] Smart learning inject: preamble now queries brain with `--like <skill>` first, then backfills with severity=error; dedup by id

## v0.6 (M2.5b) cut list — shipped 2026-06-08

- [x] 4 voter commands: `/plan-design-review` (designer + accessibility-lead), `/privacy-audit` (privacy-officer), `/compliance-check` (compliance-officer), `/benchmark` (perf-eng)
- [x] 4 ship-pipeline commands: `/land-and-deploy` (devops + oncall-sre + release-manager), `/canary` (devops + oncall-sre), `/freeze`, `/unfreeze` (release-manager)
- [x] `/ship` now reads `<repo>/.claude/skills/hivestack/FREEZE` and refuses unless the PR carries the `allow_label` (default `hotfix`)
- [x] `bin/hivestack-auto-update` — per-clone fast-forward of vendored copy. Honours throttle (1/hour), MODE marker (required-only), FREEZE lockfile, WIP guard. Verified all 4 skip branches.
- [x] `hivestack-preamble` now invokes auto-update on session start (silent unless an update was applied)

## v0.5 (M2.3 + M2.4) cut list — shipped 2026-06-08

- [x] 12 new roles: `coo`, `cfo`, `ux-researcher`, `designer`, `tech-writer`, `backend-eng`, `frontend-eng`, `data-eng`, `perf-eng`, `accessibility-lead`, `privacy-officer`, `compliance-officer`
- [x] 5 new tool stubs: `swarm-design`, `swarm-bench`, `swarm-scrape`, `swarm-pdf`, `swarm-bridge` (each: SKILL.md + bin + Python src; same stub pattern as swarm-browse v0.1)
- [x] `_charter.md`: 23/23 roles registered, council table expanded with `/plan-design-review`, `/privacy-audit`, `/compliance-check`, `/benchmark`
- [x] All 23 roles + all 8 tools accounted for — original target hit

## v0.4 (M2.5a) cut list — shipped 2026-06-08

- [x] `bin/hivestack-pretool-hook` — parses Claude Code PreToolUse JSON, calls `swarm-guard check`, emits deny JSON + exit 2 for blocks
- [x] `bin/hivestack-team-init` — writes `.claude/settings.json`, idempotent, merges with existing hooks/permissions
- [x] `./setup --team [required|optional]` flag
- [x] `docs/HOOKS.md` — install, settings shape, fail-open semantics, no-bypass-by-design rationale
- [x] Fail-open verified: invalid JSON / missing guard / timeout → rc=0 + diagnostic, never wedges session
- [ ] (M2.5b) auto-update: per-clone git fetch check on session start

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
