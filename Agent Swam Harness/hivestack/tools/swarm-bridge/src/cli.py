"""swarm-bridge — multi-agent router with driver loader.

Drivers are declared in YAML under ../../agents/. Each driver kind:
  - cli   : invokes a CLI binary with a prompt argv (claude, codex, gemini…)
  - mock  : returns a canned response (tests / fallback)
  - acp/mcp/http: reserved for M4

Routing modes:
  route <role> <prompt>     pick by role_affinity, capability, health
  run --backend X <prompt>  invoke a specific driver

No external deps — YAML parsed with a tiny stdlib-only loader (sufficient for
this schema; not a general YAML parser).
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.2.0"

INSTALL = Path(os.environ.get(
    "HIVESTACK_INSTALL",
    os.path.expanduser("~/.claude/skills/hivestack"),
))
AGENTS_DIR = INSTALL / "agents"
HOME = Path(os.environ.get("HIVESTACK_HOME", os.path.expanduser("~/.hivestack")))


# ---------- tiny YAML reader (subset; just enough for agents/*.yaml) -----

def _parse_yaml(text: str) -> dict:
    """Minimal flat-ish YAML reader for our schema.

    Supports: top-level scalars, nested dicts (one level), lists of strings,
    list-of-dicts via `- key: val`, `${ENV}` substitution. Anything richer
    isn't needed here.
    """
    out: dict = {}
    cur_key: str | None = None
    cur_list: list | None = None
    cur_dict: dict | None = None

    def expand(s: str) -> str:
        # ${VAR} substitution from environment; unknown → empty string
        out = []
        i = 0
        while i < len(s):
            if s[i:i + 2] == "${":
                j = s.find("}", i)
                if j > 0:
                    out.append(os.environ.get(s[i + 2:j], ""))
                    i = j + 1
                    continue
            out.append(s[i])
            i += 1
        return "".join(out)

    def coerce(v: str):
        v = v.strip()
        if v.startswith("'") and v.endswith("'"):
            return v[1:-1]
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        if v.lower() == "true":
            return True
        if v.lower() == "false":
            return False
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            return expand(v)

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0:
            if ":" in stripped:
                k, _, v = stripped.partition(":")
                k = k.strip()
                v = v.strip()
                cur_key = k
                cur_list = None
                cur_dict = None
                if v == "":
                    # Nested block follows
                    out[k] = None
                elif v == "{}":
                    out[k] = {}
                elif v == "[]":
                    out[k] = []
                else:
                    out[k] = coerce(v)
        else:
            if cur_key is None:
                continue
            # List item
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                if out.get(cur_key) is None:
                    out[cur_key] = []
                if ":" in item and not (item.startswith('"') or item.startswith("'")):
                    k2, _, v2 = item.partition(":")
                    out[cur_key].append({k2.strip(): coerce(v2)})
                else:
                    out[cur_key].append(coerce(item))
            else:
                # Nested dict
                if ":" in stripped:
                    k2, _, v2 = stripped.partition(":")
                    if out.get(cur_key) is None:
                        out[cur_key] = {}
                    if isinstance(out[cur_key], dict):
                        out[cur_key][k2.strip()] = coerce(v2)
    return out


# ---------- driver model -----------------------------------------------

@dataclass
class Driver:
    name: str
    kind: str
    binary: str
    args: list = field(default_factory=list)
    env: dict = field(default_factory=dict)
    capabilities: list = field(default_factory=list)
    context_window: int = 0
    cost_per_mtok_in: float = 0.0
    cost_per_mtok_out: float = 0.0
    role_affinity: list = field(default_factory=list)
    path: str = ""


def load_drivers() -> list[Driver]:
    if not AGENTS_DIR.is_dir():
        return []
    drivers: list[Driver] = []
    for p in sorted(AGENTS_DIR.glob("*.yaml")):
        try:
            d = _parse_yaml(p.read_text())
        except Exception:
            continue
        # Capabilities may be a list of strings OR a list of {name: bool} dicts.
        caps_raw = d.get("capabilities") or []
        caps: list = []
        for c in caps_raw:
            if isinstance(c, str):
                caps.append(c)
            elif isinstance(c, dict):
                for k, v in c.items():
                    if v:
                        caps.append(k)
        drivers.append(Driver(
            name=d.get("name", p.stem),
            kind=d.get("kind", "cli"),
            binary=d.get("binary", ""),
            args=d.get("args") or [],
            env=d.get("env") or {},
            capabilities=caps,
            context_window=int(d.get("context_window") or 0),
            cost_per_mtok_in=float(d.get("cost_per_mtok_in") or 0),
            cost_per_mtok_out=float(d.get("cost_per_mtok_out") or 0),
            role_affinity=d.get("role_affinity") or [],
            path=str(p),
        ))
    return drivers


def healthy(d: Driver) -> bool:
    if d.kind == "mock":
        return True
    if d.kind == "cli":
        if not d.binary:
            return False
        return shutil.which(d.binary) is not None
    return False


# ---------- dispatch ---------------------------------------------------

def dispatch(driver: Driver, prompt: str) -> dict:
    started = time.time()
    if driver.kind == "mock":
        return {
            "backend": driver.name,
            "ok": True,
            "output": f"[mock:{driver.name}] would handle: {prompt[:80]}",
            "elapsed_ms": int((time.time() - started) * 1000),
        }
    if driver.kind != "cli":
        return {"backend": driver.name, "ok": False, "error": f"unsupported kind {driver.kind!r}"}
    if shutil.which(driver.binary) is None:
        return {"backend": driver.name, "ok": False, "error": f"binary {driver.binary!r} not on PATH"}
    cmd = [driver.binary, *driver.args, prompt]
    env = os.environ.copy()
    for k, v in driver.env.items():
        if v:
            env[k] = v
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
        return {
            "backend": driver.name,
            "ok": proc.returncode == 0,
            "rc": proc.returncode,
            "output": proc.stdout,
            "stderr": proc.stderr if proc.stderr else None,
            "elapsed_ms": int((time.time() - started) * 1000),
        }
    except subprocess.TimeoutExpired:
        return {"backend": driver.name, "ok": False, "error": "timeout"}
    except Exception as e:
        return {"backend": driver.name, "ok": False, "error": str(e)}


def pick_driver(role: str | None, drivers: list[Driver]) -> Driver | None:
    if role:
        for d in drivers:
            if role in d.role_affinity and healthy(d):
                return d
    for d in drivers:
        if healthy(d) and d.kind != "mock":
            return d
    for d in drivers:
        if d.kind == "mock":
            return d
    return None


# ---------- subcommands -------------------------------------------------

def cmd_list(_):
    out = []
    for d in load_drivers():
        out.append({
            "name": d.name,
            "kind": d.kind,
            "healthy": healthy(d),
            "capabilities": d.capabilities,
            "context_window": d.context_window,
            "role_affinity": d.role_affinity,
        })
    print(json.dumps({"backends": out}, indent=2))
    return 0


def cmd_health(args):
    drivers = {d.name: d for d in load_drivers()}
    d = drivers.get(args.backend)
    if not d:
        print(f"swarm-bridge: unknown backend {args.backend!r}", file=sys.stderr)
        return 2
    print(json.dumps({"backend": d.name, "kind": d.kind, "healthy": healthy(d)}))
    return 0


def cmd_route(args):
    driver = pick_driver(args.role, load_drivers())
    if driver is None:
        print("swarm-bridge: no driver available", file=sys.stderr)
        return 2
    res = dispatch(driver, args.prompt)
    print(json.dumps(res))
    return 0 if res.get("ok") else 1


def cmd_run(args):
    drivers = {d.name: d for d in load_drivers()}
    d = drivers.get(args.backend)
    if not d:
        print(f"swarm-bridge: unknown backend {args.backend!r}", file=sys.stderr)
        return 2
    res = dispatch(d, args.prompt)
    print(json.dumps(res))
    return 0 if res.get("ok") else 1


def cmd_cost_quote(args):
    drivers = {d.name: d for d in load_drivers()}
    d = drivers.get(args.backend)
    if not d:
        print(f"swarm-bridge: unknown backend {args.backend!r}", file=sys.stderr)
        return 2
    # 4 chars/token is the well-worn industry rule of thumb.
    in_tokens = max(1, len(args.prompt) // 4)
    # Assume model produces ~equal token count back (worst-case bias toward
    # warning the caller).
    out_tokens = in_tokens
    usd = (in_tokens * d.cost_per_mtok_in + out_tokens * d.cost_per_mtok_out) / 1_000_000
    print(json.dumps({
        "backend": d.name,
        "estimated_tokens_in": in_tokens,
        "estimated_tokens_out": out_tokens,
        "estimated_usd": round(usd, 6),
        "note": "rule-of-thumb estimate, 4 chars/token, ~1:1 in:out",
    }, indent=2))
    return 0


def cmd_version(_):
    print(f"swarm-bridge {VERSION}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="swarm-bridge")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("route", help="dispatch by role affinity")
    r.add_argument("role")
    r.add_argument("prompt")
    r.set_defaults(func=cmd_route)

    run = sub.add_parser("run", help="invoke a specific backend")
    run.add_argument("--backend", required=True)
    run.add_argument("prompt")
    run.set_defaults(func=cmd_run)

    sub.add_parser("list-backends", help="list configured drivers").set_defaults(func=cmd_list)

    h = sub.add_parser("health", help="check one backend")
    h.add_argument("backend")
    h.set_defaults(func=cmd_health)

    cq = sub.add_parser("cost-quote", help="estimate USD for a prompt")
    cq.add_argument("--backend", required=True)
    cq.add_argument("prompt")
    cq.set_defaults(func=cmd_cost_quote)

    sub.add_parser("version").set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
