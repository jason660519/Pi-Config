"""swarm-design — HTML mockup + variant scaffolding.

v0.2 ships:
  - new <slug>: scaffold a session dir under ~/.hivestack/projects/<repo>/design/<slug>/
  - variants <slug> --n N: emit N HTML variant files using a built-in
    Tailwind-CDN-based template (no build step, opens in any browser)
  - gallery <slug>: write a gallery.html that links to all variants
  - list-templates / list-sessions

Screenshot rendering and visual diff land in M3 (will reuse swarm-browse
Playwright). Until then the gallery is the deliverable.

No third-party deps. Templates are Python strings.
"""
from __future__ import annotations
import argparse, html, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.2.0"
HOME = Path(os.environ.get("HIVESTACK_HOME", os.path.expanduser("~/.hivestack")))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_slug() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        return Path(out).name if out else "unknown"
    except Exception:
        return "unknown"


def session_dir(slug: str) -> Path:
    return HOME / "projects" / repo_slug() / "design" / slug


# Three deliberate aesthetic variants. Each picks a single dominant choice so
# `/plan-design-review` has actually-different things to critique.
TEMPLATES = {
    "minimal": {
        "label": "Minimal — heavy whitespace, single accent",
        "body_class": "bg-white text-zinc-900",
        "extra": "",
    },
    "dense": {
        "label": "Dense — utility-first, info density",
        "body_class": "bg-zinc-50 text-zinc-900",
        "extra": "",
    },
    "dark-prosumer": {
        "label": "Dark prosumer — high contrast, monospace UI",
        "body_class": "bg-zinc-950 text-zinc-100",
        "extra": "font-mono",
    },
}


def render_variant(slug: str, template: str, title: str, primary_action: str) -> str:
    t = TEMPLATES[template]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{html.escape(title)} — {html.escape(template)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
<style>:root {{ color-scheme: light dark; }}</style>
</head>
<body class="{t['body_class']} {t['extra']} antialiased min-h-screen">
<header class="border-b border-zinc-200/50 dark:border-zinc-800/50">
  <nav class="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
    <div class="font-semibold tracking-tight">{html.escape(slug)}</div>
    <div class="text-sm opacity-60">design variant: {html.escape(template)}</div>
  </nav>
</header>

<main class="max-w-3xl mx-auto px-6 py-16">
  <h1 class="text-4xl font-semibold tracking-tight">{html.escape(title)}</h1>
  <p class="mt-4 text-lg opacity-70">
    A {html.escape(t['label'].lower())} take.
    Replace this paragraph with the actual feature copy from the PRD.
  </p>

  <div class="mt-10 flex items-center gap-3">
    <button class="px-5 py-2.5 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 font-medium hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2">
      {html.escape(primary_action)}
    </button>
    <button class="px-5 py-2.5 rounded-lg border border-zinc-300 dark:border-zinc-700 opacity-80 hover:opacity-100">
      Cancel
    </button>
  </div>

  <section class="mt-16 grid sm:grid-cols-3 gap-6 text-sm">
    <div class="rounded-xl border border-zinc-200/60 dark:border-zinc-800/60 p-4">
      <div class="text-xs uppercase tracking-wider opacity-60">Empty state</div>
      <div class="mt-2">When the user has nothing here yet. Don't say "no data".</div>
    </div>
    <div class="rounded-xl border border-zinc-200/60 dark:border-zinc-800/60 p-4">
      <div class="text-xs uppercase tracking-wider opacity-60">Loading state</div>
      <div class="mt-2">A specific skeleton, not a spinner.</div>
    </div>
    <div class="rounded-xl border border-zinc-200/60 dark:border-zinc-800/60 p-4">
      <div class="text-xs uppercase tracking-wider opacity-60">Error state</div>
      <div class="mt-2">What happened. What the user can do. Retry button.</div>
    </div>
  </section>
</main>

<footer class="max-w-6xl mx-auto px-6 py-12 text-xs opacity-50">
  swarm-design {VERSION} · {utc_now()} · template: {html.escape(template)}
</footer>
</body></html>
"""


def render_gallery(slug: str, variants: list[Path]) -> str:
    items = "\n".join(
        f'<li><a class="block p-4 rounded-lg border hover:bg-zinc-50 dark:hover:bg-zinc-900" '
        f'href="{html.escape(v.name)}">{html.escape(v.stem)}</a></li>'
        for v in variants
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(slug)} — gallery</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 antialiased">
<main class="max-w-3xl mx-auto px-6 py-12">
<h1 class="text-2xl font-semibold tracking-tight">{html.escape(slug)}</h1>
<p class="mt-2 opacity-70">{len(variants)} variant(s) — open each, paste a Loom or screenshot into the design-review artifact.</p>
<ul class="mt-8 grid gap-2">{items}</ul>
<p class="mt-12 text-xs opacity-50">generated {utc_now()} by swarm-design {VERSION}</p>
</main></body></html>
"""


def cmd_new(args):
    d = session_dir(args.slug)
    d.mkdir(parents=True, exist_ok=True)
    (d / "BRIEF.md").write_text(
        f"# Design brief: {args.slug}\n\n"
        f"Created: {utc_now()}\n\n"
        "## Problem\n_one sentence_\n\n"
        "## User + moment\n_persona + when they hit this_\n\n"
        "## Primary action (single, named)\n_verb the user takes_\n\n"
        "## Notes for variants\n- minimal: ...\n- dense: ...\n- dark-prosumer: ...\n"
    )
    print(json.dumps({"slug": args.slug, "dir": str(d), "brief": str(d / "BRIEF.md")}, indent=2))
    return 0


def cmd_variants(args):
    d = session_dir(args.slug)
    if not d.is_dir():
        print(f"swarm-design: no session at {d}; run `swarm-design new {args.slug}` first",
              file=sys.stderr)
        return 1
    templates = list(TEMPLATES.keys())
    n = min(args.n, len(templates))
    out: list[dict] = []
    for i, tpl in enumerate(templates[:n], start=1):
        v = d / f"{i:02d}-{tpl}.html"
        v.write_text(render_variant(args.slug, tpl, args.title or args.slug,
                                    args.primary or "Continue"))
        out.append({"file": str(v), "template": tpl})
    # update gallery
    files = sorted(d.glob("[0-9][0-9]-*.html"))
    (d / "gallery.html").write_text(render_gallery(args.slug, files))
    print(json.dumps({"slug": args.slug, "variants": out,
                      "gallery": str(d / "gallery.html")}, indent=2))
    return 0


def cmd_gallery(args):
    d = session_dir(args.slug)
    if not d.is_dir():
        print(f"swarm-design: no session at {d}", file=sys.stderr)
        return 1
    files = sorted(d.glob("[0-9][0-9]-*.html"))
    (d / "gallery.html").write_text(render_gallery(args.slug, files))
    print(json.dumps({"gallery": str(d / "gallery.html"),
                      "variant_count": len(files)}, indent=2))
    return 0


def cmd_list_sessions(_):
    base = HOME / "projects" / repo_slug() / "design"
    if not base.is_dir():
        print(json.dumps({"sessions": []}, indent=2))
        return 0
    sessions = sorted([p.name for p in base.iterdir() if p.is_dir()])
    print(json.dumps({"repo": repo_slug(), "sessions": sessions}, indent=2))
    return 0


def cmd_list_templates(_):
    out = [{"name": k, "label": v["label"]} for k, v in TEMPLATES.items()]
    print(json.dumps(out, indent=2))
    return 0


def cmd_version(_):
    print(f"swarm-design {VERSION}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="swarm-design")
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("slug"); n.set_defaults(func=cmd_new)
    v = sub.add_parser("variants")
    v.add_argument("slug"); v.add_argument("--n", type=int, default=3)
    v.add_argument("--title"); v.add_argument("--primary")
    v.set_defaults(func=cmd_variants)
    g = sub.add_parser("gallery"); g.add_argument("slug"); g.set_defaults(func=cmd_gallery)
    sub.add_parser("list-sessions").set_defaults(func=cmd_list_sessions)
    sub.add_parser("list-templates").set_defaults(func=cmd_list_templates)
    sub.add_parser("version").set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
