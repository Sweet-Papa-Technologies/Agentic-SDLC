# Changelog

All notable changes to the `fofo` plugin are documented here. This project adheres
to [Semantic Versioning](https://semver.org).

## [1.0.0-beta.2] — 2026-06-21

### Fixed
- `selftest`: `test_high_patterns_match_aws_and_pem` unpacked `secret-scan`'s
  `HIGH_PATTERNS` (3-tuples) as 2-tuples, erroring the suite and turning the
  sample-feature smoke red. Corrected the unpack so all 21 self-tests pass.

### CI / tooling
- Added `.github/workflows/ci.yml` and a `.githooks/pre-push` gate that both run
  `selftest` + the sample-feature and security-gates smoke suites, so the repo
  can't be pushed or merged red. Enable the hook with
  `git config core.hooksPath .githooks`.

### Added
- **`secret-scan`** gate (Tier 0, language-agnostic, key-free) — deterministically
  flags hard-coded secrets: AWS access key IDs and PEM private-key headers hard-fail,
  secret-looking assignments escalate. Allowlist + custom patterns via
  `policy.gates.secret-scan`. Dogfooded through the loop itself (see
  `examples/security-gates`).
- **`flake-gate`** gate (Tier 0, language-agnostic, opt-in) — re-runs the suite N
  times and fails on a non-deterministic result. A flaky test is an untrustworthy
  test; run it after green to judge whether the green is *stable*. Reuses
  `redgreen-gate.test_command` unless overridden.
- **`diff-budget`** gate (Tier 0, language-agnostic, opt-in) — caps changed lines so
  a PR stays reviewable (Phase 7). Auto-selects git-numstat mode in a work tree and
  falls back to line-counting the `--changed` files; over budget escalates (waivable).
  Promotes the former bring-your-own snippet to a kept gate.
- **`selftest`** harness — fast stdlib-`unittest` coverage of the gate internals
  (`gatelib` helpers + each gate's pure decision logic), complementing the
  black-box `smoke.sh`. Runs in well under a second with no model or suite spawned.
- Smoke test extended with checks for `selftest`, `flake-gate`, and `diff-budget`;
  `policy.schema.json` documents the new gates' options.

## [1.0.0-beta.1] — 2026-06-20

First public **beta**. The skill and all gates run end to end (the smoke test passes);
the beta label invites real-world use and feedback before a stable 1.0.0.

### Added
- **`/fofo:sdlc` skill** — test-first agentic SDLC loop with separated authorship
  and judgment (Operator / Judge / Author / Referee roles, 8-phase flow).
- **Tiered gate runner** (`gate-runner`) — runs gates fail-fast in tier order,
  aggregates one JSON verdict, and routes escalations (`code` → Author,
  `tests` → Judge, `spec` → Operator).
- **Language-agnostic gates** (on by default): `spec-lint`, `trace-gate`,
  `redgreen-gate`.
- **`intent-gate`** — anti-gaming test-quality analysis for JS/TS with a **real AST**
  via a vendored `acorn` parser (zero user install) and automatic token-based
  fallback for TypeScript/JSX.
- **`separation-gate`** — enforces Author ≠ Judge from a provenance manifest.
- **Model gates** (opt-in): `semantic-test-judge`, `fresh-eyes-review`, using only
  the user-configured endpoint (Anthropic Messages shape, `base_url` override).
- **Bring-your-own gates** — `mutation` / `coverage` / `lint` wired via config; an
  `adapter` wraps any pass/fail command into the gate contract.
- **Judge & Reviewer subagents** — auto-load with the plugin.
- **Branding** — logo, icon set, social banner, and architecture diagram.
- **Docs** — README, INSTALL, gate contract, phases & roles, porting guide,
  build/design notes, and a runnable end-to-end smoke test.

[1.0.0-beta.2]: https://github.com/Sweet-Papa-Technologies/Agentic-SDLC/releases/tag/fofo--v1.0.0-beta.2
[1.0.0-beta.1]: https://github.com/Sweet-Papa-Technologies/Agentic-SDLC/releases/tag/fofo--v1.0.0-beta.1
