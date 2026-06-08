---
name: swarm-pdf
kind: tool
version: 0.2.0
description: Markdown → HTML → PDF for release notes, security reports, design specs.
allowed-tools:
  - Bash
  - Read
triggers:
  - export to pdf
  - print this report
  - pdf release notes
preferred-backends:
  - claude
---

## What it is

The `tech-writer` and `release-manager` roles need PDFs of release notes,
security audits, and design specs. v0.2 ships a working pipeline:

1. **Markdown → HTML** via a small stdlib-only subset (headings, lists,
   paragraphs, code fences, inline code, bold / italic / links, hr).
2. **HTML → PDF** via the first available engine on PATH:
   `chrome --headless --print-to-pdf`, `google-chrome`, `chromium`,
   or `wkhtmltopdf`. The macOS Chrome app bundle path is also tried.
3. **Fallback**: if no PDF engine available, the HTML is left next to the
   requested PDF path with an actionable install hint.

No third-party Python deps.

## CLI

```bash
swarm-pdf render <markdown-file> [--out <path>] [--title <text>] [--template default]
swarm-pdf list-templates
swarm-pdf version
```

## Live as of v0.2

- ✅ `render` — markdown → HTML → PDF round-trip via Chrome (verified
      against `~/.hivestack/projects/Project/specs/*.md` artifacts;
      ~190KB PDF for a 100-line markdown file).
- ✅ Fallback path: HTML kept when no PDF engine is on PATH.
- ✅ Single built-in template `default` (clean serif body, monospace code,
      14px/1.55 line height, 720px max-width).

Not yet:

- ❌ Multiple templates (Diátaxis-aligned tutorial / how-to / reference /
      explanation densities) — M3.
- ❌ Header / footer / page numbers — M3.
- ❌ Image embedding from remote URLs — M3 (needs swarm-scrape integration).

## Storage

```
~/.hivestack/projects/<slug>/releases/<branch>-<ts>.pdf   (caller picks --out)
~/.hivestack/projects/<slug>/security/<branch>-audit.pdf  (caller picks --out)
```

## Roadmap

- M2.5 (this) — markdown subset + Chrome / wkhtmltopdf shell-out
- M3 — Diátaxis templates + page chrome (header/footer/numbers)
- M3 — image embedding from URLs (via swarm-scrape)
