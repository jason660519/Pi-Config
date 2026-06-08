---
name: swarm-scrape
kind: tool
version: 0.2.0
description: Polite stdlib-only HTTP fetcher with robots.txt + rate-limit.
allowed-tools:
  - Bash
  - Read
triggers:
  - scrape this
  - extract data from
  - crawl
preferred-backends:
  - claude
---

## What it is

A polite, structured fetcher the `ux-researcher` or `pm` role can ask for
("pull competitor pricing pages"). v0.2 uses stdlib `urllib` + a tiny
HTMLParser-based link extractor. No third-party deps.

## CLI

```bash
swarm-scrape fetch <url> [--json] [--with-body] [--ignore-robots] [--insecure]
swarm-scrape crawl <seed-url> --depth N [--domain-only] [--ignore-robots]
swarm-scrape robots <url>
swarm-scrape version
```

## Behaviour

- **Honours `robots.txt`** by default. `--ignore-robots` explicitly bypasses
  (it's a flag, not a default — easier to audit).
- **Per-domain rate limit**: one request every 2 seconds, in-process.
- **User-Agent**: `hivestack-swarm-scrape/0.2 (+repo URL)`.
- **macOS Python SSL workaround**: macOS Python ships without a CA bundle by
  default, causing `CERTIFICATE_VERIFY_FAILED` on first run. `--insecure`
  skips verify as a one-line workaround; the right fix is to run
  `Install Certificates.command` from the Python install dir.

## Live as of v0.2

- ✅ `fetch` — real HTTP GET, returns `{ok, url, status, content_type, bytes, body, robots, ts}`
- ✅ `crawl` — bounded breadth-first, optional `--domain-only`
- ✅ `robots` — pure verdict ("allow" / "disallow" / "unreachable")
- ✅ Rate limit + UA + robots all enforced unless overridden
- ✅ Title + link extraction via stdlib `html.parser`

Not yet:

- ❌ JS-rendered pages (would share `swarm-browse` Playwright backend in M3)
- ❌ Authenticated sessions (cookie import via `swarm-browse` in M3)
- ❌ Schema-driven extraction (`parse --schema <yaml>` planned for M3)

## Storage

Crawl output goes to stdout (one JSON-line per visited URL). No persistent
storage in v0.2; callers redirect to a file if they want one.

## Roadmap

- M2.5 (this) — stdlib fetcher + robots + rate-limit
- M3 — JS rendering via swarm-browse; authenticated session cookies
- M3 — `parse --schema` for structured extraction
