---
name: swarm-design
kind: tool
version: 0.2.0
description: HTML mockup + variant scaffolding (3 Tailwind templates, no build step).
allowed-tools:
  - Bash
  - Read
triggers:
  - generate ui variants
  - mockup this
  - design html
preferred-backends:
  - claude
---

## What it is

The `designer` role's hands. v0.2 emits three deliberately-distinct
single-file HTML variants (Tailwind via CDN — no build step), plus a gallery
page that links to all of them. Screenshot + diff land in M3 (will reuse
swarm-browse Playwright).

## CLI

```bash
swarm-design new <slug>                              # scaffold session + BRIEF.md
swarm-design variants <slug> [--n 3] [--title T] [--primary "Save changes"]
swarm-design gallery <slug>                          # regenerate gallery.html
swarm-design list-sessions
swarm-design list-templates
swarm-design version
```

## Built-in templates (3, deliberately different)

| Template | Aesthetic choice |
|---|---|
| `minimal` | Heavy whitespace, single accent, white-on-zinc |
| `dense` | Utility-first, information density |
| `dark-prosumer` | High contrast, monospace UI, dark default |

Each variant ships all three required UI states (empty / loading / error) as
inert blocks so `/plan-design-review` has them to critique without the
designer being able to hand-wave "we'll add those later".

## Live as of v0.2

- ✅ `new`, `variants`, `gallery`, `list-sessions`, `list-templates`
- ✅ Real HTML files written under
      `~/.hivestack/projects/<repo>/design/<slug>/`
- ✅ Gallery page links variants in `01-…`, `02-…` order
- ✅ Tailwind via CDN — opens cleanly in Chrome / Safari without npm

Not yet:

- ❌ Screenshots (M3, via swarm-browse Playwright)
- ❌ Visual diff between variants (M3)
- ❌ AI-generated variants (M3, via swarm-bridge → designer role)

## Storage

```
~/.hivestack/projects/<repo>/design/<slug>/
  ├── BRIEF.md                  problem / user / primary action
  ├── 01-minimal.html
  ├── 02-dense.html
  ├── 03-dark-prosumer.html
  └── gallery.html
```

## Roadmap

- M2.5 (this) — three template scaffolds + gallery
- M3 — Playwright screenshots + perceptual diff
- M3 — AI-generated variants routed through swarm-bridge
- M4 — image-based design critique by `designer` role on screenshots
