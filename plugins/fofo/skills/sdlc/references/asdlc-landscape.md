# Where FoFo sits in the agentic-SDLC landscape

One honest page. The 2026 agentic-SDLC world has converged on a few named
methodologies; this is what each owns, what none of them owns, and exactly how
FoFo docks into them. FoFo is **not** a spec framework, a planning methodology,
or an agent-team orchestrator — it is the **test-integrity layer underneath
whichever of those you already use**.

## The map

| Framework / tool | What it owns | Enforcement mechanism | Test integrity? |
|---|---|---|---|
| **GitHub Spec Kit** | specify → plan → tasks artifacts (`spec.md`, FR-### requirements) feeding any coding agent | markdown the agent is trusted to follow | none — trusts the agent's tests |
| **Kiro** (AWS) | spec-driven IDE: requirements (EARS) → design → tasks | IDE workflow + prose | none |
| **BMAD-METHOD** | 12+ role agents (PM, architect, QA, SM) across the full lifecycle, file-based handoffs | agent personas + templates | none |
| **AWS AI-DLC** | rituals: intent → Mob Elaboration → Units of Work → Bolts, human validates each step | ceremony + human checkpoints | none |
| **TDD-Guard** | red → green → refactor *ordering* (no code without a failing test) | hooks that block out-of-order edits | ordering only — can't catch a test authored to match the code, or a weak test |
| **Mutation testing** (Stryker, mutmut, …) | "do the tests *catch* bugs" — the gold standard for assertion strength | mutants + kill rate | strong but slow; nothing about *who* wrote the tests or *how* |
| **FoFo** | test integrity: who wrote the tests, whether they can be trusted, whether the process was honest | **scripts with exit codes** (gate contract), separated contexts, hash locks | yes — that's the whole product |

Two structural observations fall out of this table:

1. **Everyone upstream trusts the agent's tests.** Every SDD framework hands a
   beautiful spec to an agent and accepts "tests pass" as done. 2026
   reward-hacking research (SpecBench, the Verification Horizon paper, the RHB
   suite) showed why that's not enough: agents skip verification steps, read
   leaked answers, hardcode expectations, and tamper with the very functions
   that grade them — and trajectory-level monitoring plus independent judging
   collapses those hacked-pass rates by an order of magnitude. FoFo is that
   layer, packaged: separation (`separation-gate`), tamper evidence
   (`test-lock`), oversight protection (`oversight-integrity`), test-quality
   grading (`intent-gate`, `semantic-test-judge`), and process auditing
   (`trajectory-judge`).
2. **Enforcement by prose doesn't survive contact with an optimizing agent.**
   Personas, rituals, and instructions get summarized away under context
   pressure. FoFo's rules are executables that exit non-zero; the only prose is
   choreography.

## Docking points (use them together)

- **Spec Kit / Kiro / BMAD → FoFo.** Author the spec there; import it here:
  `scripts/spec-adapter --input spec.md` converts FR-### bullets, EARS
  requirements docs, and BMAD PRDs into the `REQUIREMENTS.md` the loop
  consumes. `spec-lint` also reads EARS criteria (`WHEN … THEN the system
  SHALL …`) natively, so Kiro-style specs lint unmodified.
- **AI-DLC → FoFo.** A Unit of Work is a natural FoFo run; `diff-budget` is the
  same small-slice discipline as a Bolt, enforced by exit code. Run the gate
  runner as each Bolt's exit criterion.
- **TDD-Guard + FoFo.** Complementary, not competing: TDD-Guard polices cycle
  *order* in the editor; FoFo verifies authorship separation and test quality
  at the gate. Nothing conflicts — run both.
- **Mutation testing inside FoFo.** Not absorbed, wrapped: point the `mutation`
  BYO gate at your mutation tool and its kill-rate verdict routes through the
  same escalation pipeline as every other gate.
- **Any CI.** The runner emits one JSON verdict and one exit code — wire it as
  a required check and the loop's guarantees survive outside the editor.

## What FoFo deliberately refuses to own

Specify/plan/task decomposition, role-agent zoos, dashboards, hosted services.
Those lanes are crowded and well-served. The moat is narrow and deep:
**the context that grades the work is not the context that did the work, and
every rule that must hold is a script with an exit code.**
