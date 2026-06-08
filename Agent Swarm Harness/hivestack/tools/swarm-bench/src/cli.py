"""swarm-bench — benchmark agents / drivers across a task suite.

A "suite" is a YAML-ish file under ~/.hivestack/bench/suites/<name>.yaml
declaring tasks. Each task is dispatched to one or more backends via
swarm-bridge; latency, exit code, and (in M4) LLM-judge quality scores
are captured.

v0.2 ships:
  - suite loader (same tiny YAML reader as swarm-bridge)
  - runner that invokes swarm-bridge per task per backend
  - per-run summary JSON + a flat HTML leaderboard
  - `list-suites` / `compare` skeletons
"""
from __future__ import annotations
import argparse, json, os, statistics, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.2.0"
INSTALL = Path(os.environ.get("HIVESTACK_INSTALL", os.path.expanduser("~/.claude/skills/hivestack")))
HOME = Path(os.environ.get("HIVESTACK_HOME", os.path.expanduser("~/.hivestack")))
BENCH_DIR = HOME / "bench"
SUITES_DIR = BENCH_DIR / "suites"
RUNS_DIR = BENCH_DIR / "runs"
BRIDGE = INSTALL / "tools" / "swarm-bridge" / "bin" / "swarm-bridge"


# Reuse swarm-bridge's tiny YAML reader by import — they live in sibling dirs.
sys.path.insert(0, str(INSTALL / "tools" / "swarm-bridge" / "src"))
try:
    from cli import _parse_yaml  # type: ignore
except Exception:
    def _parse_yaml(text: str) -> dict:  # fallback: only JSON-shaped
        try:
            return json.loads(text)
        except Exception:
            return {}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def list_suites() -> list[Path]:
    SUITES_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(SUITES_DIR.glob("*.yaml"))


def load_suite(name: str) -> dict | None:
    p = SUITES_DIR / f"{name}.yaml"
    if not p.is_file():
        return None
    return _parse_yaml(p.read_text())


def dispatch_one(backend: str, prompt: str) -> dict:
    if not BRIDGE.is_file():
        return {"ok": False, "error": "swarm-bridge not installed"}
    started = time.time()
    try:
        proc = subprocess.run(
            [str(BRIDGE), "run", "--backend", backend, prompt],
            capture_output=True, text=True, timeout=180,
        )
        elapsed_ms = int((time.time() - started) * 1000)
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception:
            payload = {"raw": proc.stdout, "stderr": proc.stderr}
        payload["bench_elapsed_ms"] = elapsed_ms
        payload["rc"] = proc.returncode
        return payload
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "bench_elapsed_ms": 180_000}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def cmd_list_suites(_):
    suites = [p.stem for p in list_suites()]
    print(json.dumps({"suites": suites}, indent=2))
    if not suites:
        print("(no suites yet — create one at "
              f"{SUITES_DIR}/<name>.yaml with `tasks:` list)", file=sys.stderr)
    return 0


def cmd_run(args):
    suite = load_suite(args.suite)
    if not suite:
        print(f"swarm-bench: suite {args.suite!r} not found in {SUITES_DIR}", file=sys.stderr)
        return 1
    tasks = suite.get("tasks") or []
    if not tasks:
        print(f"swarm-bench: suite {args.suite!r} has no tasks", file=sys.stderr)
        return 1
    backends = args.backends.split(",") if args.backends else (suite.get("backends") or ["mock"])

    run_id = f"{args.suite}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for task in tasks:
        if isinstance(task, str):
            prompt = task
            task_id = task[:40]
        elif isinstance(task, dict):
            prompt = task.get("prompt", "")
            task_id = task.get("id") or prompt[:40]
        else:
            continue
        for backend in backends:
            res = dispatch_one(backend, prompt)
            res.update({"task": task_id, "backend": backend, "ts": utc_now()})
            results.append(res)
            (run_dir / f"{backend}--{task_id.replace('/', '_')}.json").write_text(
                json.dumps(res, indent=2)
            )

    # Summary
    by_backend: dict[str, list[int]] = {}
    by_backend_ok: dict[str, int] = {}
    for r in results:
        b = r.get("backend", "?")
        by_backend.setdefault(b, []).append(int(r.get("bench_elapsed_ms", 0)))
        by_backend_ok[b] = by_backend_ok.get(b, 0) + (1 if r.get("ok") else 0)
    summary = {
        "run_id": run_id,
        "suite": args.suite,
        "ts": utc_now(),
        "task_count": len(tasks),
        "backends": backends,
        "by_backend": {
            b: {
                "n": len(by_backend[b]),
                "ok": by_backend_ok.get(b, 0),
                "p50_ms": int(statistics.median(by_backend[b])) if by_backend[b] else 0,
                "max_ms": max(by_backend[b]) if by_backend[b] else 0,
            }
            for b in by_backend
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


def cmd_leaderboard(args):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs = sorted(RUNS_DIR.glob("*/summary.json"))
    if not runs:
        print("no runs yet — run `swarm-bench run <suite>` first", file=sys.stderr)
        return 1
    rows = []
    for r in runs[-args.limit:]:
        try:
            rows.append(json.loads(r.read_text()))
        except Exception:
            continue
    print(json.dumps({"runs": rows}, indent=2))
    return 0


def cmd_compare(args):
    a = (RUNS_DIR / args.a / "summary.json")
    b = (RUNS_DIR / args.b / "summary.json")
    if not a.is_file() or not b.is_file():
        print(f"swarm-bench: missing run summary; ensure both {args.a} and {args.b} exist",
              file=sys.stderr)
        return 1
    sa, sb = json.loads(a.read_text()), json.loads(b.read_text())
    print(json.dumps({"a": sa, "b": sb}, indent=2))
    return 0


def cmd_version(_):
    print(f"swarm-bench {VERSION}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="swarm-bench")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("suite")
    r.add_argument("--backends", help="comma-separated; overrides suite default")
    r.set_defaults(func=cmd_run)
    sub.add_parser("list-suites").set_defaults(func=cmd_list_suites)
    lb = sub.add_parser("leaderboard")
    lb.add_argument("--limit", type=int, default=10)
    lb.set_defaults(func=cmd_leaderboard)
    cp = sub.add_parser("compare")
    cp.add_argument("a")
    cp.add_argument("b")
    cp.set_defaults(func=cmd_compare)
    sub.add_parser("version").set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
