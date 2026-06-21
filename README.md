<p align="center">
  <img src="./assets/banner.png" alt="FoFo — Agentic SDLC" width="100%">
</p>

<p align="center">
  <a href="#install"><img src="https://img.shields.io/badge/Claude%20Code-plugin-1b2440?style=flat-square&labelColor=10b78f" alt="Claude Code plugin"></a>
  <img src="https://img.shields.io/badge/version-1.0.0--beta.1-7fe3cb?style=flat-square" alt="version 1.0.0-beta.1">
  <img src="https://img.shields.io/badge/status-beta-f5a623?style=flat-square" alt="beta">
  <img src="https://img.shields.io/badge/license-MIT-10b78f?style=flat-square" alt="MIT license">
  <img src="https://img.shields.io/badge/deps-Python%203%20%2B%20Node-1b2440?style=flat-square" alt="deps">
  <img src="https://img.shields.io/badge/stack-agnostic-f5a623?style=flat-square" alt="stack-agnostic">
</p>

<h1 align="center">FoFo — Agentic SDLC</h1>

<p align="center">
  <b>A test-first development loop for AI coding agents, where the context that <i>grades</i> the tests is kept separate from the one that writes the code — and every rule that must hold is a script with a real exit code, not a sentence the model is trusted to honor.</b>
</p>

---

## Why

AI agents write tests that pass. That's the problem. A test the same context wrote to match the code it just wrote proves almost nothing — it locks in behavior without judging it. FoFo fixes the *trust* of your tests:

- An **independent context (the Judge)** writes the tests from the spec, **before any code exists**.
- A **separate context (the Author)** writes code to pass tests it didn't write and **cannot silently weaken**.
- A **gate runner (the Referee)** grades the **code _and_ the tests** — assertion intent, traceability, mutation, separation — and escalates to a human **only what the gates can't resolve**.

Procedure lives in the skill. **Enforcement lives in scripts with real exit codes**, so it can't be summarized away or gamed.

## Install

In [Claude Code](https://code.claude.com):

```text
/plugin marketplace add Sweet-Papa-Technologies/Agentic-SDLC
/plugin install fofo@fofo-marketplace
```

Then use it with `/fofo:sdlc`, or just describe a spec-to-code task ("implement this from the spec", "write tests TDD") and Claude loads it automatically. The **Judge** and **Reviewer** subagents auto-load — check `/agents`.

> Works on **Claude Code** out of the box; the same folder is format-compatible with other `SKILL.md`-consuming agents (Cursor, Codex CLI, Gemini CLI). See [INSTALL.md](./plugins/fofo/skills/sdlc/INSTALL.md).

## How it works

<p align="center">
  <img src="./assets/architecture.png" alt="FoFo phase/role flow" width="100%">
</p>

Four roles, run as separate contexts where the host allows:

| Role | Who | Sees | Never does |
|------|-----|------|------------|
| **Operator** | the human | everything | owns spec sign-off, escalations, security |
| **Judge** | sub-agent, spec-only | spec + test intents | see the implementation |
| **Author** | separate context | tests + code | edit the tests that grade it |
| **Referee** | gate scripts | the diff | make calls scripts can't |

When verification fails, the runner tags each escalation with a **route**: `code` failures go back to the Author, `tests` failures go back to the Judge in a fresh pass. **The Author never edits the tests that grade it.**

## The gates

Every gate — kept or bring-your-own — obeys one I/O contract (`--changed --policy`, prints one JSON verdict, exits `0` pass / `1` fail / `2` escalate / `3` skip). Mix and match; point config at your stack.

| Gate | Tier | What it checks | Default |
|------|:----:|----------------|:-------:|
| `spec-lint` | 0 | every requirement has an ID + acceptance criteria | ✅ on |
| `trace-gate` | 0 | every requirement maps to ≥1 test; flags orphan tests | ✅ on |
| `redgreen-gate` | 0 | suite is red before code, green after | ✅ on |
| `intent-gate` | 0 | catches assertion-free / trivially-true / snapshot-only / banned-mock tests — **real AST** (vendored parser) for JS/TS, token fallback for TS/JSX | ✅ on |
| `separation-gate` | 0 | fails if one context authored both the tests and the code for a unit | ⚙️ opt-in |
| `flake-gate` | 0 | re-runs the suite N times; fails if the result is non-deterministic (a flaky test is an untrustworthy test) | ⚙️ opt-in |
| `diff-budget` | 0 | caps changed lines so a PR stays small enough to actually review (Phase 7); git-diff or line-count mode | ⚙️ opt-in |
| `mutation` · `coverage` · `lint` | 0 | **bring your own** command, wrapped to the contract | ⚙️ opt-in |
| `semantic-test-judge` | 1 | model judges whether each test asserts requirement *intent* vs. just touching lines | ⚙️ opt-in |
| `fresh-eyes-review` | 1 | model scans the diff for cheating, security, silent architecture changes | ⚙️ opt-in |

No mutation/coverage/lint/model-proxy/language is hardcoded. Heavy and model gates are **disabled by default**, so a fresh install runs the language-agnostic gates immediately with nothing else installed.

## Quickstart (per repo)

```bash
# 1. drop in the config (one time, from the installed plugin dir)
cp "$HOME/.claude/plugins/marketplaces/fofo-marketplace/plugins/fofo/skills/sdlc/gates.config.example" gates.config
cp "$HOME/.claude/plugins/marketplaces/fofo-marketplace/plugins/fofo/skills/sdlc/policy.json" policy.json

# 2. point red/green at your test command (policy.json -> gates.redgreen-gate.test_command)

# 3. run the whole gate runner over your changes
"$HOME/.claude/plugins/.../skills/sdlc/scripts/gate-runner" \
  --config gates.config --changed "src/**/* test/**/*"
```

Or just run `/fofo:sdlc` and let the skill choreograph the phases.

## What's in the box

```
Agentic-SDLC/                         # project home AND plugin marketplace
├── .claude-plugin/marketplace.json   # this catalog
├── assets/                           # logo, banner, icons, diagram
└── plugins/fofo/
    ├── .claude-plugin/plugin.json    # plugin manifest
    ├── agents/                       # Judge + Reviewer subagents (auto-load)
    └── skills/sdlc/                  # the skill: SKILL.md, gate scripts, references, a runnable smoke test
```

Deep docs ship with the skill:
[`SKILL.md`](./plugins/fofo/skills/sdlc/SKILL.md) ·
[gate contract](./plugins/fofo/skills/sdlc/references/gate-contract.md) ·
[phases & roles](./plugins/fofo/skills/sdlc/references/phases.md) ·
[porting to other languages](./plugins/fofo/skills/sdlc/references/porting-to-other-languages.md) ·
[design notes](./plugins/fofo/skills/sdlc/BUILD-NOTES.md)

## Verify it yourself

The skill ships a runnable end-to-end smoke test (no API key needed — the model gate is exercised against a local mock):

```bash
cd plugins/fofo/skills/sdlc/examples/sample-feature && bash smoke.sh
# -> ALL CHECKS PASSED
```

For a fast inner-loop check of the gate internals (no model, no test suite spawned), run the unit harness:

```bash
python3 plugins/fofo/skills/sdlc/scripts/selftest
# -> OK
```

## Updating

Bump `version` in `plugins/fofo/.claude-plugin/plugin.json` and the matching entry in `.claude-plugin/marketplace.json`, commit, tag with `claude plugin tag ./plugins/fofo`, and push. Users get it via `/plugin marketplace update fofo-marketplace`.

## Contributing & License

Contributions welcome — see [CONTRIBUTING.md](./CONTRIBUTING.md). Brand assets and usage in [BRANDING.md](./BRANDING.md).

MIT © 2026 Forrester Terry. Bundles [acorn](https://github.com/acornjs/acorn) (MIT). See [LICENSE](./LICENSE).
