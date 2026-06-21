# Phases & Roles — full detail

Offloaded from SKILL.md. The skill body is the choreography; this is the reference.

## Files the loop reads and writes

| File | Owner | Purpose |
|------|-------|---------|
| `SPEC.md` / `DESIGN.md` / `REQUIREMENTS.md` | Operator | The spec. `REQUIREMENTS.md` carries the IDs + acceptance criteria the gates parse. |
| `TEST-REQS.yaml` | Judge | Requirement ID → test intents (Phase 1 output). |
| test files | Judge | The tests, each tagged with a requirement ID (Phase 2). |
| `src/` (or your layout) | Author | The implementation (Phase 3). |
| `PROVENANCE.yaml` | host/orchestrator | Who authored tests vs code per unit (enables `separation-gate`). |
| `gates.config`, `policy.json` | Operator | Orchestration and thresholds. |

## Conventions the gates expect

### REQUIREMENTS.md

Each requirement is a block introduced by a heading/bullet that contains its ID,
followed by an acceptance criterion:

```markdown
### REQ-001: Reject empty input
The parser must reject empty input.
Acceptance: parse("") raises an error rather than returning a value.

### REQ-002: Trim whitespace
Acceptance: parse("  a  ") returns "a".
```

`spec-lint` fails if a requirement has no ID or no `Acceptance:` line. The ID
pattern and the acceptance label are configurable (`policy.gates.spec-lint`).

### TEST-REQS.yaml (Phase 1)

Any format works as long as the requirement IDs appear in it; `trace-gate` matches
on the IDs. A readable convention:

```yaml
REQ-001:
  - intent: empty input raises, no value returned
REQ-002:
  - intent: leading/trailing whitespace trimmed
```

### Test tagging (Phase 2)

The requirement ID must appear in each test — in the test name or a comment:

```js
it("REQ-001 rejects empty input", () => { ... });    // name carries the ID
// @req: REQ-002
test("trims whitespace", () => { ... });
```

`trace-gate` reports a requirement with no tagged test (under-coverage) and a test
referencing an unknown ID (orphan).

## Phase-by-phase

### Phase 0 — Spec & Design (Operator)
Exit: `spec-lint` passes. No requirement without an ID + acceptance criterion.

### Phase 1 — Test Requirements (Judge, spec only)
The Judge sub-agent sees only the spec. It writes `TEST-REQS.yaml`.
Exit: `trace-gate` — every requirement ID has ≥1 intent.

### Phase 2 — Test Authoring (Judge, tests first)
The Judge writes tests tagged with requirement IDs. They are red (no code yet).
Exit: `redgreen-gate --expect red`. A red caused by a load/collection/syntax error
(rather than missing behavior) is flagged "red for the wrong reason" and escalates.

### Phase 3 — Implementation (Author, separate context)
A different context writes code to green. The Author does not touch the tests.
Exit: `redgreen-gate --expect green` (suite green).

### Phase 4 — Verification (Referee, Tier 0)
`gate-runner` runs the enabled Tier-0 gates fail-fast in tier order:
`trace-gate`, `intent-gate`, `redgreen-gate`, and if enabled `mutation`,
`coverage`, `separation-gate`, `flake-gate`. One aggregate verdict; one exit code.
`flake-gate` re-runs the suite N times and fails on a non-deterministic result —
run it after green, since it judges whether the green is *stable*, not whether it's
green. Exit: all hard gates pass or escalate.

### Phase 5 — Fresh-Eyes Review (Referee, Tier 1, third context)
With model gates enabled, the run continues into `semantic-test-judge` (do the
tests assert intent, or just touch lines?) and `fresh-eyes-review` (cheat /
security / silent-architecture scan). Run from a Reviewer sub-agent isolated from
Author and Judge context.
Exit: clean or escalate.

### Phase 6 — Human Escalation (Operator, Tier 2)
Hand the Operator the runner's `escalation` array only — each item is
`{gate, route, summary, confidence, findings[]}`. A decision payload, not raw
diffs. The Operator resolves; nothing else proceeds until they do.

### Phase 7 — Integration
Keep PRs reviewable, then merge. The kept **diff-budget** gate caps how much a
change touches (a diff a human can't hold doesn't get a real review). Enable it and
set the budget:

```json
{ "name": "diff-budget", "tier": 0, "enabled": true, "script": "diff-budget", "waivable": true }
```
```json
// policy.gates.diff-budget
{ "max_lines": 400, "base_ref": "HEAD", "count_mode": "auto", "on_exceed": "escalate" }
```

It auto-selects git-diff mode in a work tree (added+deleted vs `base_ref`) and falls
back to counting the `--changed` files' lines when there's no repo. Being `waivable`,
an over-budget change escalates to the Operator instead of hard-blocking — a big
change can still ship once a human signs off on the size.

## Loop-back routing

`gate-runner` tags each escalation with a `route`:

| Gate | Route | Goes to |
|------|-------|---------|
| `redgreen-gate` (green fail), `mutation`, `lint`, `fresh-eyes-review` | `code` | **Author** |
| `trace-gate`, `intent-gate`, `semantic-test-judge`, `separation-gate`, `flake-gate` | `tests` | **Judge** (fresh pass) |
| `diff-budget` | `review` | **Operator** (size sign-off) |
| `spec-lint` | `spec` | **Operator** |

The Author fixes code; the Judge fixes tests. The Author never edits the tests
that grade it — a test that looks wrong is an escalation to the Judge, not an edit.

## Tiers

- **Tier 0** — cheap, deterministic, language-agnostic (or BYO). Run on every change.
- **Tier 1** — model-based, slower, off by default. Run when Tier 0 is clean.
- **Tier 2** — the human. Only what the gates could not resolve.
