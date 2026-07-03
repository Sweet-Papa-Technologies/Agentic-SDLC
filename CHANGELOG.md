# Changelog

All notable changes to the `fofo` plugin are documented here. This project adheres
to [Semantic Versioning](https://semver.org).

## [1.0.0-beta.4] — 2026-07-03

Process-auditing + nondeterministic-code release: the loop can now judge *how*
the code was produced, not just what it looks like, and hold LLM-app code to
eval floors instead of one-shot red/green.

### Added
- **`trajectory-judge`** gate (Tier 1, model-based, opt-in) — the model reads
  the Author's exported transcript (`policy.gates.trajectory-judge.transcript_file`)
  and hunts six cheat signals: intent-to-game, test-tampering,
  hardcoded-expectation, forbidden-channel, oversight-tampering, misreporting.
  High-confidence signals hard-fail; anything suspicious escalates to the
  Operator (`route: review`). Trajectory-level monitoring is the strongest
  countermeasure in 2026 reward-hacking research; this packages it behind the
  standard gate contract. Head+tail truncation keeps long transcripts in budget.
- **`eval-gate`** gate (Tier 0, language-agnostic, opt-in) — red/green for
  nondeterministic code. Runs a BYO `eval_command` N trials and holds the
  aggregate to floors: `min_pass_rate` over exit codes, and optionally
  `min_score` over a mean score extracted from stdout via `score_regex` (e.g.
  a golden-dataset accuracy). One green run of a probabilistic unit proves
  nothing; N runs against a floor is a verdict.
- **`references/asdlc-landscape.md`** — one-page honest positioning: what
  Spec Kit / Kiro / BMAD / AI-DLC / TDD-Guard / mutation testing each own, why
  none of them owns test integrity, and the concrete docking points for using
  FoFo underneath each.
- Smoke test extended with checks for `test-lock`, `eval-gate`, and
  `trajectory-judge`; the mock model endpoint is now prompt-aware so both
  Tier-1 gate shapes are exercised without an API key. `selftest` 42 → 56.

### Fixed
- `diff-budget` (git mode) now expands `--changed` globs to real file paths
  before handing them to git: git's pathspec wildmatch treats `src/**/*`
  differently from the shell and could silently match nothing, under-counting
  the diff to 0 lines. Found by the beta.4 end-to-end run.

## [1.0.0-beta.3] — 2026-07-03

Agentic-integrity + SDD-interop release: closes the gaps 2026 reward-hacking
research says are real (test tampering, oversight sabotage, silent dependency
additions) and docks FoFo under the spec-driven-development tools (Spec Kit,
Kiro, BMAD) instead of competing with them.

### Added
- **`test-lock`** gate (Tier 0, language-agnostic, on by default) — tamper
  evidence for the loop's central promise. At Phase 2 exit the Judge runs
  `test-lock --write`, hashing the test files (sha256) into `TEST-LOCK.json`;
  from then on a modified or deleted locked test **hard-fails** and a test file
  that appears after the lock **escalates**. "The Author never edits the tests
  that grade it" is now a checked fact, not a procedure. Skips harmlessly until
  a lock exists.
- **`oversight-integrity`** gate (Tier 0, language-agnostic, on by default,
  waivable) — the referee protects its own machinery. Fails if the diff touches
  `gates.config`, `policy.json`, `policy.schema.json`, `PROVENANCE.*`, or
  `TEST-LOCK.json` (patterns configurable). Git-diff mode with a `--changed`
  fallback outside a work tree. Waivable so a deliberate Operator config change
  escalates for sign-off instead of hard-stopping.
- **`deps-gate`** gate (Tier 0, language-agnostic, on by default) — a new
  dependency escalates for Operator sign-off. Name-level diff of `package.json`,
  `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, and `Gemfile`
  against the git base ref. Skips outside a git work tree.
- **`spec-adapter`** converter — imports specs authored for other SDD tools into
  the `REQUIREMENTS.md` the loop consumes: GitHub Spec Kit `spec.md` (FR-###
  bullets), Kiro `requirements.md` (EARS acceptance criteria), and BMAD PRDs
  (FR#/NFR# lines). Auto-detects the format; flags requirements that arrive
  without a verifiable criterion.
- **EARS support in `spec-lint`** — an EARS-format criterion
  (`WHEN <trigger> THEN the system SHALL <response>`) now satisfies a
  requirement even without the `Acceptance:` label (`accept_ears`, default on),
  so Kiro-style specs lint without rewriting.
- New escalations route `review` → Operator (integrity violations and dependency
  sign-off are human calls, not something the Author or Judge self-resolves).
- `selftest` doubled (21 → 42 tests) covering the new gates' pure logic and all
  three spec-adapter converters; `policy.schema.json` documents the new options.

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

[1.0.0-beta.4]: https://github.com/Sweet-Papa-Technologies/Agentic-SDLC/releases/tag/fofo--v1.0.0-beta.4
[1.0.0-beta.3]: https://github.com/Sweet-Papa-Technologies/Agentic-SDLC/releases/tag/fofo--v1.0.0-beta.3
[1.0.0-beta.2]: https://github.com/Sweet-Papa-Technologies/Agentic-SDLC/releases/tag/fofo--v1.0.0-beta.2
[1.0.0-beta.1]: https://github.com/Sweet-Papa-Technologies/Agentic-SDLC/releases/tag/fofo--v1.0.0-beta.1
