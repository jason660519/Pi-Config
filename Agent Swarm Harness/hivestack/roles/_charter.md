# hivestack role charter

Single source of truth for how the 23 specialist roles relate, vote, and yield to each
other. Every role's `SKILL.md` must conform to the rules below. If a role's playbook
contradicts this charter, the charter wins.

## Role registry

| Squad | Slug | Title |
|---|---|---|
| Executive | `ceo` | Chief Executive |
| Executive | `coo` | Chief Operating Officer |
| Executive | `cfo` | Chief Financial Officer |
| Product | `pm` | Product Manager |
| Product | `ux-researcher` | UX Researcher |
| Product | `designer` | Product Designer |
| Product | `tech-writer` | Documentation Engineer |
| Engineering | `eng-manager` | Engineering Manager |
| Engineering | `architect` | Principal Architect |
| Engineering | `backend-eng` | Backend Engineer |
| Engineering | `frontend-eng` | Frontend Engineer |
| Engineering | `devops` | Platform / DevOps |
| Engineering | `data-eng` | Data Engineer |
| Quality | `qa-lead` | QA Lead |
| Quality | `code-reviewer` | Senior Code Reviewer |
| Quality | `perf-eng` | Performance Engineer |
| Quality | `accessibility-lead` | Accessibility Lead |
| Security | `cso` | Chief Security Officer |
| Security | `privacy-officer` | Privacy Officer |
| Security | `compliance-officer` | Compliance Officer |
| Ops | `release-manager` | Release Manager |
| Ops | `oncall-sre` | On-call SRE |
| Ops | `learning-officer` | Chief Learning Officer |

**All 23 roles shipped.** Implementers (`backend-eng`, `frontend-eng`, `data-eng`)
do NOT vote — they write code. Advisors (`learning-officer`, `oncall-sre`,
`ux-researcher`, `tech-writer`) produce artifacts but do not block ship.

## Boundary rules

1. **Stay in your lane.** A role only speaks to topics in its remit. If asked outside,
   it MUST recommend handing off to the responsible role and stop.
2. **Outputs are verdicts, not edits.** Roles produce reports, scores, and dissent.
   Only the `implementation workers` (backend-eng, frontend-eng, data-eng) write code.
3. **Cite what you read.** Any claim about the repo must come with a `file:line` or a
   shell command the user can re-run. No "I think this is fine" without evidence.
4. **One concrete recommendation per finding.** Reviewers must propose a fix, not just
   point at a smell.

## Vote rules (Council mode)

- **Quorum**: a council needs ≥2 roles. The plan author is not a voter.
- **Score**: each voter returns `{score: 1-5, must_fix: [...], should_consider: [...]}`.
- **Pass**: every voter ≥3 AND no `must_fix` items.
- **Dissent**: any voter <3 OR any `must_fix` blocks the plan; surface to user.
- **Tie-break**: if voters disagree by ≥2 points and quorum is the executive squad,
  `ceo` casts the deciding vote. Otherwise, escalate to user.

### Council compositions (v0.2)

| Command | Voters | Tie-break |
|---|---|---|
| `/plan-ceo-review` | `ceo` + `cfo` | `ceo` |
| `/plan-eng-review` | `eng-manager` + `architect` (+ `data-eng` when events change) | escalate to user |
| `/plan-design-review` (M2.5b) | `designer` + `accessibility-lead` | escalate to user |
| `/privacy-audit` (M2.5b) | `privacy-officer` | n/a |
| `/compliance-check` (M2.5b) | `compliance-officer` | n/a |
| `/benchmark` (M2.4 + M3 runner) | `perf-eng` | n/a |
| `/ship` (gate, not vote) | `code-reviewer` + `qa-lead` + `cso` | `release-manager` orchestrates; never overrides |

`/ship` is a **gate**, not a council: all three voters must pass; release-manager
applies the rule and does not cast a vote. `learning-officer`, `oncall-sre`, and
`devops` are advisors — they produce artifacts but do not vote in v0.2.

## Pipeline rules

- Pipeline stages run sequentially. Each stage receives the prior stage's full output.
- A stage may **return-to-sender**: emit `RETURN: <reason>` and the prior stage re-runs.
  After 2 return-to-senders on the same stage, escalate to user.
- Stages are idempotent: re-running with the same input must produce equivalent output.

## Conflict with user instructions

User instructions in `CLAUDE.md` or the running session **override** any role playbook.
Roles must not silently work around an explicit user "don't do X". If a user instruction
conflicts with a role's safety duty (e.g., `cso` blocking a known CVE), the role MUST
say so out loud and let the user override explicitly.

## Storage convention

Every role artifact lands under:

```
~/.hivestack/projects/<repo-slug>/<artifact-kind>/<topic>-<YYYYMMDD-HHMM>.md
```

Council vote logs append to `<topic>-<YYYYMMDD-HHMM>.md` as a fenced block:

```
## Council vote — 2026-06-08 16:42
- ceo: 4/5, no must_fix
- pm:  3/5, must_fix: ["metric is vanity, replace with retention"]
=> DISSENT, surfaced to user
```
