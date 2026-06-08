---
name: pair
kind: command
version: 0.1.0
description: Run the same task on two backends via swarm-bridge; diff the outputs.
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - pair this
  - dual run
  - claude vs codex
  - second opinion
preferred-backends:
  - claude
tools_invoked:
  - swarm-bridge
---

## When to invoke

When you want a second-opinion implementation, or you're evaluating which
backend handles a class of task better. Useful for non-trivial code-edit
prompts where two backends might disagree on approach.

## Preamble

```bash
source <(~/.claude/skills/hivestack/bin/hivestack-preamble --skill pair \
  2>/dev/null || ./hivestack/bin/hivestack-preamble --skill pair)
```

## Inputs

- `<prompt>` — the task. Quote it.
- `--a <backend>` — first backend (default: `claude`)
- `--b <backend>` — second backend (default: `codex`)

## Steps

1. **Check both backends healthy** via `swarm-bridge health <name>`.
   If either is unhealthy, refuse and name the missing backend.
2. **Cost quote** via `swarm-bridge cost-quote --backend <a>` and `--backend <b>`.
   Sum the two; if `swarm-guard budget status` shows remaining < sum, ask
   user to confirm via `AskUserQuestion`.
3. **Dispatch in parallel** to both backends:
   ```bash
   ~/.claude/skills/hivestack/tools/swarm-bridge/bin/swarm-bridge \
     run --backend "$A" "$PROMPT" > "$OUT_A" &
   ~/.claude/skills/hivestack/tools/swarm-bridge/bin/swarm-bridge \
     run --backend "$B" "$PROMPT" > "$OUT_B" &
   wait
   ```
4. **Render side-by-side**: parse both JSON responses, present `output`
   fields under headed columns. If one backend errored, surface the error
   clearly — don't pretend the other backend's answer is canonical.
5. **Write the pair report** to
   `~/.hivestack/projects/<slug>/pair/<topic>-<YYYYMMDD-HHMM>.md`
   with both outputs verbatim, elapsed_ms each, and the prompt.
6. **Ask the user to pick** via `AskUserQuestion` which output (if any) to
   adopt. We never auto-apply a pair output to files.

## Output

- Pair report artifact path.
- Side-by-side render in chat.
- One-line picked-result line (`adopted: <backend>`, or `adopted: neither`).

## Failure modes

- One backend down: surface clearly, do NOT silently fall back to the
  healthy one — that defeats the point of pairing.
- Both down: refuse, recommend `swarm-bridge list-backends` to triage.
- Massive output (>50KB total): truncate the render but keep full text in
  the artifact.

## Hand-off

If the user adopts an output, suggest `/review` against the result before
shipping — pairing produces options, not verdicts.
