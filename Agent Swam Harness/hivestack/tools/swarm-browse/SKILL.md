---
name: swarm-browse
kind: tool
version: 0.1.0
description: Headless browser for QA, dogfooding, and screenshot capture. (hivestack)
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

**v0.1 stub.** Prints planned actions to stdout. Real Playwright/CDP backend lands in
M1.5. Stub mode lets `/qa` and `/design-review` rehearse their flows end-to-end without
the heavy browser dependency.

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

- M1.5 — Playwright backend, single-tab CDP, screenshot diff
- M2 — sidecar prompt-injection classifier (port from gstack `browse/`)
- M2 — cookie import for authenticated dogfooding
- M3 — multi-tab and parallel sessions
