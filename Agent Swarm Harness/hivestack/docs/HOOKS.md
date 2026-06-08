# PreToolUse hook — wiring swarm-guard into Claude Code

`hivestack-pretool-hook` is a Claude Code PreToolUse hook that runs
`swarm-guard check` against every Bash command BEFORE Claude Code executes it.
Block-class commands (`rm -rf /`, `git push --force main`, `git add .env`, …)
get denied with the reason surfaced to the user; warn-class commands pass
through with a stderr nudge; everything else is silent.

## What you get

```text
User session ─► Claude wants to run Bash:  rm -rf /
                       │
                       ▼
              PreToolUse hook fires
                       │
                       ▼
              swarm-guard check 'rm -rf /'
                       │
                       ▼  rc=2 + reason on stderr
              hook emits JSON deny + exit 2
                       │
                       ▼
              Claude Code refuses to run; user sees:
                "[block] rm-root: filesystem wipe (rm -rf /, rm -rf $HOME)"
```

Fail-open: if the hook can't read its input, can't find `swarm-guard`, or
hits a timeout, it exits 0 with a `[hivestack-pretool-hook] fail-open: …`
diagnostic on stderr. A broken hook never wedges your session.

## Install

### One-shot (current repo, recommended)

```bash
# from inside your repo:
./.claude/skills/hivestack/setup --team        # required mode
./.claude/skills/hivestack/setup --team optional
```

The `setup --team` flag does two things:

1. Symlinks / copies hivestack to `~/.claude/skills/hivestack` (user-global).
2. Runs `hivestack-team-init` in the current git repo, which writes
   `<repo>/.claude/settings.json` with the PreToolUse hook entry.

### Manual

```bash
cd <your-repo>
~/.claude/skills/hivestack/bin/hivestack-team-init required
```

That command is **idempotent** and **merges** — it preserves any other hooks,
permissions, or settings you already have in `.claude/settings.json`.

## Settings.json shape after install

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/skills/hivestack/bin/hivestack-pretool-hook"
          }
        ]
      }
    ]
  }
}
```

`${CLAUDE_PROJECT_DIR}` is expanded by Claude Code at hook invocation time.
This means the hook works against the **vendored** copy inside the repo,
not the user-global one — so contributors who don't have hivestack installed
globally still get the protection as long as they cloned the repo and ran
`./.claude/skills/hivestack/setup`.

## What the hook is, and isn't

It IS:

- a static-pattern check on the literal command string
- a defence against typos and obvious foot-guns (`rm -rf $UNSET_VAR/`)
- the place to land "we agreed never to do X" rules across a team

It is NOT:

- a sandbox — it doesn't intercept syscalls, it doesn't see what a binary
  *does*, only what was typed
- exhaustive — there will always be ways to express dangerous intent that
  the regex doesn't catch. Treat it as one layer.

## Verifying the hook is active

Run these in Claude Code; the first should succeed, the second should be
blocked with a visible reason:

```text
# safe
ls -la

# dangerous — hook should block
rm -rf /
```

If `rm -rf /` runs without the hook firing, the hook isn't installed in this
repo. Re-run `hivestack-team-init`.

## Bypassing for one command

There is **no built-in bypass flag** by design — bypass-mode features tend to
become the default. If you genuinely need to run something the hook blocks
and you accept the risk, edit the rule out of `tools/swarm-guard/src/guard.py`
in this repo, run that one command, and revert. The 60-second friction is the
point.

## Uninstall

```bash
# remove just the hook entry from this repo:
~/.claude/skills/hivestack/bin/hivestack-team-init optional
# then manually trim .claude/settings.json if you want it gone entirely.

# remove the whole install:
~/.claude/skills/hivestack/setup --uninstall
```
