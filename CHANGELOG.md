# Changelog

All notable changes to the `fofo` plugin are documented here. This project adheres
to [Semantic Versioning](https://semver.org).

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

[1.0.0-beta.1]: https://github.com/Sweet-Papa-Technologies/Agentic-SDLC/releases/tag/fofo--v1.0.0-beta.1
