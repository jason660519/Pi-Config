---
name: swarm-browse
kind: tool
version: 0.2.0
description: Headless browser; Playwright when installed, stub otherwise (auto-detected).
allowed-tools:
  - Bash
  - Read
triggers:
  - browse this page
  - take a screenshot
  - navigate to url
  - inspect the page
preferred-backends:
  - claude
---

## Status

**v0.2 — Playwright-aware.** On startup the CLI runs `require.resolve('playwright')`:

- If Playwright is installed (`npm i playwright && npx playwright install chromium`),
  real navigation, waits, and (per-call stateless) page interaction are wired.
- If not, falls back to v0.1 stub behaviour so `/qa` and `/plan-design-review` still
  rehearse their flows end-to-end. `swarm-browse version` prints the active mode.

Stateful operations that need a persistent page (sequential `open` → `click` →
`screenshot` across separate CLI invocations) await the M3 daemon. Today, run the
sequence inside one Node script that imports the same module.

## Commands (planned API)

```bash
swarm-browse open <url>                       # baseline navigation
swarm-browse screenshot [--out <path>] [--full]
swarm-browse click <selector>
swarm-browse fill <selector> <value>
swarm-browse wait <selector> [--timeout 5000]
swarm-browse network --since <ts>             # request log
swarm-browse console --since <ts>             # browser console log
swarm-browse close
```

In v0.1 each prints `stub: <command> <args>` and exits 0, so callers can be wired
today and the real implementation slots in without touching SKILL.md call sites.

## Storage

Screenshots and HARs land under:

```
~/.hivestack/projects/<repo-slug>/qa/<feature>-<ts>/
  ├── 01-baseline.png
  ├── 02-clicked-submit.png
  ├── network.har
  └── console.txt
```

## Roadmap

- M2.5 (this) — Playwright detection + stateless `open` / `wait` / `close` live
- M3 — long-running daemon for stateful sequences across CLI invocations
- M3 — screenshot diff via perceptual hash
- M3 — sidecar prompt-injection classifier (port from gstack `browse/`)
- M3 — cookie import for authenticated dogfooding
- M4 — multi-tab + parallel sessions
