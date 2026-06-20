---
name: fofo-agentic-sdlc
description: >
  Test-first agentic development loop with separated authorship and judgment.
  Use whenever implementing a feature, fixing a bug, or writing code from a
  spec/ticket and you want the tests to be trustworthy: an independent context
  writes tests from the spec BEFORE the code, code is written against those tests,
  then the tests themselves are graded (mutation, assertion-intent, traceability)
  and only what the gates can't resolve is escalated to a human. Trigger on
  "implement", "write tests", "TDD", "build this feature", "make this pass review",
  or any spec-to-code task where test quality and review trust matter, even if not
  explicitly asked.
---

# FoFo Agentic SDLC

A test-first loop where the context that *grades* the tests is separate from the
context that *writes the code*, and every rule that must hold is a **script with
an exit code**, not a sentence you're trusted to honor.

**Core rule:** the Author writes code to pass tests it did not write and cannot
silently weaken. The Judge writes the tests from the spec, before code exists. The
Referee (gate scripts) grades code *and tests*, and routes only the unresolved to
the Operator (human).

`${CLAUDE_SKILL_DIR}` is this skill's folder. Gate scripts live in
`${CLAUDE_SKILL_DIR}/scripts/`. The user's repo holds `gates.config`, `policy.json`,
`REQUIREMENTS.md`, and the tests/code.

## Setup (once per repo)

If `gates.config` is missing at the repo root, copy the defaults in:

```bash
cp "${CLAUDE_SKILL_DIR}/gates.config.example" gates.config
cp "${CLAUDE_SKILL_DIR}/policy.json" policy.json
```

A fresh install runs the language-agnostic gates (`spec-lint`, `trace-gate`,
`redgreen-gate`, `intent-gate`) immediately. Heavy/BYO gates (mutation, coverage,
lint) and the model gates are **disabled by default** — enable them in
`gates.config` when wired up. Set `policy.gates.redgreen-gate.test_command` to the
project's test command so red/green can run.

## Roles

| Role | Who | Sees | Never does |
|------|-----|------|------------|
| **Operator** | the human | everything | — (owns spec sign-off, escalations, security) |
| **Judge** | sub-agent, spec-only | spec + `TEST-REQS.yaml` | see the implementation |
| **Author** | separate context | tests + code | edit the tests that grade it |
| **Referee** | gate scripts | the diff | make judgment calls scripts can't |

Separation is the point. Run the Judge and Reviewer as **separate contexts** (see
[Sub-agent orchestration](#sub-agent-orchestration)). Procedural separation is the
default; `separation-gate` is the enforcement upgrade.

## The loop

Each phase has an exit gate. Nothing proceeds until the gate passes or the failure
is escalated. Full detail in [references/phases.md](references/phases.md).

**Phase 0 — Spec & Design (Operator).** Inputs: `SPEC.md` / `DESIGN.md` /
`REQUIREMENTS.md`. Every requirement has a stable ID (`REQ-001`) and an
`Acceptance:` criterion.
Exit gate:
```bash
"${CLAUDE_SKILL_DIR}/scripts/spec-lint" --policy policy.json --context .
```

**Phase 1 — Test Requirements (Judge, spec only).** The Judge produces
`TEST-REQS.yaml` mapping each requirement ID to one or more test intents.
Exit gate (every requirement has ≥1 intent):
```bash
"${CLAUDE_SKILL_DIR}/scripts/trace-gate" --policy policy.json --context .
```

**Phase 2 — Test Authoring (Judge, tests first).** The Judge writes the tests,
each tagged with its requirement ID (the ID appears in the test name or a
`@req:REQ-001` comment). They are **red** because no implementation exists.
Exit gate (red, and red for the right reason):
```bash
"${CLAUDE_SKILL_DIR}/scripts/redgreen-gate" --expect red --policy policy.json --context .
```

**Phase 3 — Implementation (Author, separate context).** A *different* context
writes code to turn the suite green. The Author must not modify the tests. If a
test looks wrong, that is an escalation back to the Judge — not an edit.
Exit gate: suite green (`redgreen-gate --expect green`).

**Phase 4 — Verification (Referee, Tier 0).** Run the full gate runner over the
changed files:
```bash
"${CLAUDE_SKILL_DIR}/scripts/gate-runner" --config gates.config \
  --changed "src/**/* test/**/*" --context .
```
This runs the enabled Tier-0 hard gates (`trace-gate`, `intent-gate`,
`redgreen-gate`, and — if enabled — `mutation`, `coverage`, `separation-gate`)
fail-fast in tier order and prints one aggregate JSON verdict.
Exit: all hard gates pass, or escalate.

**Phase 5 — Fresh-Eyes Review (Referee, Tier 1, third context).** With the model
gates enabled, the same run continues into `semantic-test-judge` and
`fresh-eyes-review`. Run these from a Reviewer sub-agent that has seen neither the
Author's nor the Judge's working context.
Exit: clean, or escalate.

**Phase 6 — Human Escalation (Operator, Tier 2).** Hand the Operator the
`escalation` array from the runner's report — a tight decision payload (gate,
summary, route, high findings), not raw diffs. The Operator decides; they do not
re-derive.

**Phase 7 — Integration.** Keep the PR reviewable, then merge. (A `diff-budget`
check is a BYO gate you can wire via `adapter`; see references/phases.md.)

### Loop-back rule (critical)

When verification fails, the runner tags each escalation with a `route`:

- `route: code` → back to the **Author** (redgreen green-fail, mutation, lint,
  fresh-eyes). Fix the code.
- `route: tests` → back to the **Judge**, in a fresh pass (trace, intent,
  semantic-test-judge, separation). Fix the tests.

**Never let the Author edit the tests that grade it.** Test problems go to the
Judge; code problems go to the Author.

## Sub-agent orchestration

Separate the contexts. Detect capability first.

> Installed as the `fofo` plugin? The Judge and Reviewer subagents auto-load — they
> already appear in `/agents`, so skip the copy step below.

**If the host has native sub-agents (Claude Code — this is the concrete path):**

- **Judge sub-agent.** Spawn a sub-agent (Task/Agent tool, or a definition in
  `.claude/agents/` — copy the ready ones from
  `${CLAUDE_SKILL_DIR}/agents/fofo-judge.md` and `fofo-reviewer.md`). Hand it
  **only** the spec and `TEST-REQS.yaml`. It writes the test requirements and the
  tests. It must not be given the implementation.
- **Author = the main context** (or its own sub-agent) that never receives the
  Judge's reasoning — only the finished tests.
- **Reviewer sub-agent.** For Phase 5, spawn a sub-agent that sees the diff but
  neither the Author's nor the Judge's working context.

Restrict tools so a role can't step outside it (e.g. the Judge gets `Read, Write,
Grep` but is told not to read `src/`).

**If the host has no sub-agents (fallback):** run each role as a sequential
fresh-context pass (new session / cleared context). Write the Judge's outputs to
files (`TEST-REQS.yaml`, the test files), clear context, then implement. Record who
authored what in a provenance manifest and turn on `separation-gate` so the
separation is **enforced**, not just intended:

```yaml
# PROVENANCE.yaml
units:
  - unit: validator
    tests_by: judge-ctx-2026-06-20T09:00
    code_by: author-ctx-2026-06-20T10:15
```

Be honest about which mode you're in. Procedural separation is the default;
`separation-gate` + a provenance manifest is the enforcement upgrade.

## Gates and the contract

Every gate — kept or bring-your-own — obeys one I/O contract: invoked with
`--changed --policy [--context] [--config]`, prints one JSON verdict, exits
`0` pass / `1` fail / `2` escalate / `3` skip / `>=10` internal error. Full spec:
[references/gate-contract.md](references/gate-contract.md).

- **Kept, language-agnostic:** `spec-lint`, `trace-gate`, `redgreen-gate`,
  `separation-gate`.
- **Kept JS/TS reference:** `intent-gate` — real-AST analysis of test quality via a
  parser **vendored with the skill** (nothing to install), with an automatic
  token-based fallback for TS/JSX. Other languages drop in their own analyzer behind
  the same contract — see
  [references/porting-to-other-languages.md](references/porting-to-other-languages.md).
- **Kept, model-based (Tier 1, off by default):** `semantic-test-judge`,
  `fresh-eyes-review`. They use only the endpoint configured in `gates.config`.
- **Bring-your-own (config, not code):** `mutation`, `coverage`, `lint`. Point
  `gates.config` at a project command. Wrap a plain pass/fail command with
  `${CLAUDE_SKILL_DIR}/scripts/adapter`.

Adapt everything in one place: `gates.config` (orchestration) and `policy.json`
(thresholds/patterns). Don't hardcode tools.

## What stays out of this file

Anything enforceable is a script, not prose here. If you find yourself asking the
model to "remember" a rule, that rule belongs in a gate.
