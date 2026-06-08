"""swarm-scrape — polite stdlib-only fetcher with robots.txt + rate-limit.

No third-party deps. Uses urllib + html.parser. Authenticated sessions and
JS rendering are deferred to M4 (would share swarm-browse Playwright).
"""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import ssl
from urllib import robotparser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

VERSION = "0.2.0"
UA = "hivestack-swarm-scrape/0.2 (+https://github.com/jason660519/Hivewire)"
HOME = Path(os.environ.get("HIVESTACK_HOME", os.path.expanduser("~/.hivestack")))
SCRAPE_DIR = HOME / "scrape"

# Conservative per-domain rate limit: one request every 2 seconds.
_last_hit: dict[str, float] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def respect_rate_limit(host: str) -> None:
    now = time.time()
    last = _last_hit.get(host, 0)
    if now - last < 2.0:
        time.sleep(2.0 - (now - last))
    _last_hit[host] = time.time()


def robots_allows(url: str, ignore: bool = False) -> tuple[bool, str]:
    if ignore:
        return True, "ignored (--ignore-robots)"
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        return True, "non-http scheme"
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        # If robots.txt unreachable, default to allow (matches most crawlers).
        return True, "robots.txt unreachable, defaulting to allow"
    allowed = rp.can_fetch(UA, url)
    return allowed, f"robots.txt: {'allow' if allowed else 'disallow'}"


class _LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.title: str = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self.links.append(v)
        elif tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def fetch(url: str, ignore_robots: bool = False, insecure: bool = False) -> dict:
    parsed = urlparse(url)
    if not parsed.scheme:
        return {"ok": False, "error": "URL has no scheme"}
    allowed, why = robots_allows(url, ignore=ignore_robots)
    if not allowed:
        return {"ok": False, "blocked_by": why, "url": url}
    respect_rate_limit(parsed.netloc)
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    # macOS Python ships without a CA bundle by default; users hit
    # CERTIFICATE_VERIFY_FAILED out of the box. --insecure skips cert verify.
    ctx = ssl._create_unverified_context() if insecure else None
    try:
        with urlopen(req, timeout=15, context=ctx) as resp:
            body = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            text = body.decode(charset, errors="replace")
            return {
                "ok": True,
                "url": resp.geturl(),
                "status": resp.status,
                "content_type": resp.headers.get("Content-Type", ""),
                "bytes": len(body),
                "body": text,
                "robots": why,
                "ts": utc_now(),
            }
    except HTTPError as e:
        return {"ok": False, "url": url, "error": f"HTTP {e.code}: {e.reason}"}
    except URLError as e:
        return {"ok": False, "url": url, "error": f"URL error: {e.reason}"}
    except Exception as e:
        return {"ok": False, "url": url, "error": str(e)}


def cmd_fetch(args):
    res = fetch(args.url, ignore_robots=args.ignore_robots, insecure=args.insecure)
    if not res.get("ok"):
        print(json.dumps(res), file=sys.stderr)
        return 1
    if args.json:
        # Strip body so JSON output is bounded; print body separately if requested
        body = res.pop("body", "")
        print(json.dumps(res))
        if args.with_body:
            sys.stdout.write(body)
        return 0
    sys.stdout.write(res["body"])
    return 0


def cmd_crawl(args):
    seed_url = args.seed
    domain = urlparse(seed_url).netloc
    if not domain:
        print("seed URL has no netloc", file=sys.stderr)
        return 1
    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(seed_url, 0)]
    out: list[dict] = []
    while queue:
        url, depth = queue.pop(0)
        if url in seen or depth > args.depth:
            continue
        seen.add(url)
        res = fetch(url, ignore_robots=args.ignore_robots, insecure=args.insecure)
        if not res.get("ok"):
            out.append({"url": url, "ok": False, "error": res.get("error") or res.get("blocked_by")})
            continue
        ex = _LinkExtractor()
        try:
            ex.feed(res.get("body", ""))
        except Exception:
            pass
        out.append({"url": res["url"], "ok": True, "status": res["status"],
                    "title": ex.title.strip()[:200], "link_count": len(ex.links)})
        if depth < args.depth:
            for href in ex.links:
                resolved = urljoin(res["url"], href)
                p = urlparse(resolved)
                if args.domain_only and p.netloc != domain:
                    continue
                if resolved not in seen:
                    queue.append((resolved, depth + 1))
    for row in out:
        print(json.dumps(row))
    return 0


def cmd_robots(args):
    allowed, why = robots_allows(args.url, ignore=False)
    print(json.dumps({"url": args.url, "allowed": allowed, "why": why}))
    return 0 if allowed else 1


def cmd_version(_):
    print(f"swarm-scrape {VERSION}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="swarm-scrape")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="fetch a single URL")
    f.add_argument("url")
    f.add_argument("--json", action="store_true",
                   help="emit metadata JSON to stdout instead of raw body")
    f.add_argument("--with-body", action="store_true",
                   help="with --json, also write body after the JSON line")
    f.add_argument("--ignore-robots", action="store_true")
    f.add_argument("--insecure", action="store_true",
                   help="skip TLS verify (workaround for macOS Python missing CA bundle)")
    f.set_defaults(func=cmd_fetch)

    c = sub.add_parser("crawl", help="bounded breadth-first crawl")
    c.add_argument("seed")
    c.add_argument("--depth", type=int, default=1)
    c.add_argument("--domain-only", action="store_true", default=True)
    c.add_argument("--ignore-robots", action="store_true")
    c.add_argument("--insecure", action="store_true")
    c.set_defaults(func=cmd_crawl)

    r = sub.add_parser("robots", help="show robots.txt verdict for a URL")
    r.add_argument("url")
    r.set_defaults(func=cmd_robots)

    sub.add_parser("version").set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
