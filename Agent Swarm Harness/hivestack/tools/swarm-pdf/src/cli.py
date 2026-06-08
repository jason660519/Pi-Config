"""swarm-pdf — markdown → HTML → PDF.

Strategy:
  1. Convert markdown → HTML via a tiny stdlib-friendly subset (headings,
     paragraphs, lists, code fences, inline code, bold, italic, links).
  2. Wrap in a styled HTML template.
  3. Render to PDF via the first available tool on PATH:
       chrome --headless --print-to-pdf
       google-chrome --headless --print-to-pdf
       wkhtmltopdf
  4. If none available, write the HTML next to the requested PDF path and
     return a friendly error pointing the user at install commands.

No third-party deps.
"""
from __future__ import annotations
import argparse, html, os, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.2.0"

HOME = Path(os.environ.get("HIVESTACK_HOME", os.path.expanduser("~/.hivestack")))


TEMPLATES = {
    "default": """<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title><style>
:root {{ color-scheme: light; }}
body {{ font: 14px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; max-width: 720px; margin: 4em auto; padding: 0 1em; color: #1a1a1a; }}
h1, h2, h3 {{ line-height: 1.2; }}
h1 {{ border-bottom: 1px solid #ddd; padding-bottom: .3em; }}
code {{ background: #f5f5f5; padding: 1px 5px; border-radius: 3px; font: 12.5px ui-monospace, SFMono-Regular, Menlo, monospace; }}
pre {{ background: #f5f5f5; padding: 1em; border-radius: 6px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
a {{ color: #0366d6; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
hr {{ border: none; border-top: 1px solid #ddd; }}
blockquote {{ border-left: 3px solid #ccc; color: #555; margin: 1em 0; padding: .2em 1em; }}
table {{ border-collapse: collapse; }}
td, th {{ border: 1px solid #ddd; padding: .35em .6em; }}
</style></head><body>
{body}
<hr>
<p style="color:#888; font-size: 12px;">Rendered by swarm-pdf {version} · {ts}</p>
</body></html>""",
}


def md_to_html(src: str) -> str:
    """Minimal CommonMark subset. Not feature-complete; safe for our use cases
    (release notes, security reports, design specs)."""
    lines = src.split("\n")
    out: list[str] = []
    in_code = False
    code_lines: list[str] = []
    code_lang = ""
    in_list = False
    list_tag = ""

    def flush_list():
        nonlocal in_list, list_tag
        if in_list:
            out.append(f"</{list_tag}>")
            in_list = False
            list_tag = ""

    def inline(t: str) -> str:
        # escape first, then re-apply markup
        t = html.escape(t, quote=False)
        # `code` (do FIRST so inside-code asterisks aren't bolded)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        # links [text](url)
        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', t)
        # bold **x**
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        # italic *x*
        t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
        return t

    for ln in lines:
        if ln.startswith("```"):
            if in_code:
                out.append(f'<pre><code class="lang-{html.escape(code_lang)}">'
                           + html.escape("\n".join(code_lines)) + "</code></pre>")
                in_code = False
                code_lines = []
                code_lang = ""
            else:
                flush_list()
                in_code = True
                code_lang = ln[3:].strip()
            continue
        if in_code:
            code_lines.append(ln)
            continue
        if ln.startswith("# "):
            flush_list()
            out.append(f"<h1>{inline(ln[2:])}</h1>")
        elif ln.startswith("## "):
            flush_list()
            out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("### "):
            flush_list()
            out.append(f"<h3>{inline(ln[4:])}</h3>")
        elif re.match(r"^\s*[-*]\s+", ln):
            if not in_list or list_tag != "ul":
                flush_list()
                out.append("<ul>")
                in_list, list_tag = True, "ul"
            out.append(f"<li>{inline(re.sub(r'^\s*[-*]\s+', '', ln))}</li>")
        elif re.match(r"^\s*\d+\.\s+", ln):
            if not in_list or list_tag != "ol":
                flush_list()
                out.append("<ol>")
                in_list, list_tag = True, "ol"
            out.append(f"<li>{inline(re.sub(r'^\s*\d+\.\s+', '', ln))}</li>")
        elif ln.strip() == "":
            flush_list()
        elif ln.strip() == "---":
            flush_list()
            out.append("<hr>")
        else:
            flush_list()
            out.append(f"<p>{inline(ln)}</p>")
    flush_list()
    return "\n".join(out)


def render_html(md: str, title: str) -> str:
    body = md_to_html(md)
    return TEMPLATES["default"].format(
        title=html.escape(title, quote=True),
        body=body,
        version=VERSION,
        ts=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def find_pdf_engine() -> tuple[str, list[str]] | None:
    """Return (binary, argv-prefix-template) for the first available engine."""
    candidates = [
        ("chrome", ["--headless", "--disable-gpu", "--no-sandbox"]),
        ("google-chrome", ["--headless", "--disable-gpu", "--no-sandbox"]),
        ("chromium", ["--headless", "--disable-gpu", "--no-sandbox"]),
        ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
         ["--headless", "--disable-gpu"]),
        ("wkhtmltopdf", []),
    ]
    for binary, args in candidates:
        if shutil.which(binary) or os.path.exists(binary):
            return binary, args
    return None


def render_pdf(html_path: Path, pdf_path: Path) -> tuple[bool, str]:
    engine = find_pdf_engine()
    if engine is None:
        return False, ("no PDF engine found; install one of: "
                       "Google Chrome (`brew install --cask google-chrome`) or "
                       "wkhtmltopdf (`brew install wkhtmltopdf`).")
    binary, args = engine
    if "wkhtmltopdf" in binary:
        cmd = [binary, "--quiet", str(html_path), str(pdf_path)]
    else:
        cmd = [binary, *args, f"--print-to-pdf={pdf_path}",
               f"file://{html_path.resolve()}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return False, f"{binary} rc={proc.returncode}: {proc.stderr.strip()[:200]}"
        return True, f"rendered via {binary}"
    except subprocess.TimeoutExpired:
        return False, f"{binary} timed out"
    except Exception as e:
        return False, f"{binary} error: {e}"


def cmd_render(args):
    src = Path(args.markdown).expanduser()
    if not src.is_file():
        print(f"swarm-pdf: not found: {src}", file=sys.stderr)
        return 1
    out = Path(args.out).expanduser() if args.out else src.with_suffix(".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    title = args.title or src.stem
    html_doc = render_html(src.read_text(encoding="utf-8"), title)
    html_tmp = out.with_suffix(".html")
    html_tmp.write_text(html_doc, encoding="utf-8")
    ok, msg = render_pdf(html_tmp, out)
    if ok:
        print(f"✓ wrote {out} ({msg}); intermediate HTML at {html_tmp}")
        return 0
    print(f"⚠ no PDF written: {msg}")
    print(f"  HTML rendered at {html_tmp}; open it in a browser and print-to-PDF manually.")
    return 1


def cmd_list_templates(_):
    print("\n".join(TEMPLATES.keys()))
    return 0


def cmd_version(_):
    print(f"swarm-pdf {VERSION}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="swarm-pdf")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("markdown")
    r.add_argument("--out")
    r.add_argument("--title")
    r.add_argument("--template", default="default")
    r.set_defaults(func=cmd_render)
    sub.add_parser("list-templates").set_defaults(func=cmd_list_templates)
    sub.add_parser("version").set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
