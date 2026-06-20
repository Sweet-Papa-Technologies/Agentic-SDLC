# Build notes

Decisions, doc conflicts resolved, and the smoke-test run.

## Step 0 — what the live docs confirmed (authoritative over the brief)

Read 2026-06-20:
- Agent Skills overview — `platform.claude.com/docs/en/agents-and-tools/agent-skills/overview`
- Claude Code skills — `code.claude.com/docs/en/skills`
- Claude Code subagents — `code.claude.com/docs/en/sub-agents`

Confirmed:
- **SKILL.md frontmatter.** Required: `name`, `description`. `name` ≤64 chars,
  lowercase/numbers/hyphens only, and **must not contain the reserved words
  "anthropic" or "claude"** — `fofo-agentic-sdlc` is compliant. `description`
  non-empty, ≤1024 chars (ours is 642). Claude-Code-specific optional fields:
  `disable-model-invocation`, `user-invocable`, `allowed-tools`,
  `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `hooks`,
  `paths`.
- **Install paths.** Personal `~/.claude/skills/<name>/SKILL.md`; project
  `.claude/skills/<name>/SKILL.md`. Directory name (not `name`) becomes the `/`
  command. Live change detection picks up edits without restart.
- **Subagents.** Defined in `.claude/agents/*.md` (project) or `~/.claude/agents/`
  (user), frontmatter `name`/`description`/`tools`/`model`. A subagent runs in its
  own context window with only its system prompt — exactly the isolation the Judge
  and Reviewer roles need. A skill can run forked (`context: fork` + `agent:`) or
  spawn subagents via the Agent/Task tool.
- **`${CLAUDE_SKILL_DIR}` substitution** resolves to the skill folder — used
  throughout SKILL.md so gate scripts are found regardless of CWD.
- **Packaging.** Zip the folder with `SKILL.md` at its root for claude.ai/API
  upload; add `.claude-plugin/plugin.json` to load as a plugin (which also
  auto-loads bundled `agents/`).

### Doc conflicts with the brief, and how they were resolved

1. **Brief shows `name:` in frontmatter as if it sets the command.** Docs: the
   command name comes from the *directory*, and `name` cannot contain "claude".
   Kept `name: fofo-agentic-sdlc` (valid; serves as display label) and rely on the
   directory name for the command. No conflict in practice.
2. **Brief's `description` is long.** Docs cap it at 1024 chars. Rewrote a tighter
   642-char description preserving every trigger word.
3. **Sub-agent "invocation contract".** The brief speculated about a spawn/fork
   API. Docs give two concrete mechanisms: `.claude/agents/` definitions and
   `context: fork`. We ship ready `agents/fofo-judge.md` and
   `agents/fofo-reviewer.md` and document copying them to `.claude/agents/`, plus
   the sequential-fallback for hosts without subagents — matching the brief's
   capability-detection requirement.
4. **Runtime/network surface.** Docs note Claude API / claude.ai skill runtimes
   have no/limited network. Recorded in INSTALL: Tier-1 model gates need a host
   with network (Claude Code); Tier-0 gates run anywhere with Python 3.

## Runtime choice

- **Kept gates: Python 3 stdlib only.** Zero third-party deps — `argparse`, `glob`,
  `json`, `subprocess`, `urllib`. A fresh install runs the language-agnostic gates
  with nothing installed beyond Python 3 and a POSIX shell.
- **`intent-gate`: Node, AST-first with automatic token fallback.** Two engines,
  chosen per file, **zero user install**:
  1. **AST (preferred)** — a real ESTree tree from **acorn 8.17.0 (MIT), vendored**
     into `scripts/vendor/acorn.js`. It ships *inside* the skill folder, so there
     is no `npm install`, no `package.json`, and no network at runtime — the parser
     travels with the skill. Test calls and assertions are matched against AST node
     shapes (`CallExpression`/`MemberExpression`), which is more precise than text
     (e.g. it now catches `assert.strictEqual(1, 1)` as trivial).
  2. **Tokens (fallback)** — the original hand-written tokenizer (strings, template
     literals incl. `${…}`, comments, and regex literals are real tokens) walking
     test bodies by brace-matching. Used automatically when acorn can't parse a
     file (TypeScript type syntax, JSX, decorators) or if the vendored parser is
     ever removed. Both engines feed one shared classifier, so verdicts match.
  - The gate reports which engine ran per invocation, e.g.
    `… [engine ast:1]` or `… [engine tokens(fallback):1]`.
  - **Why vendoring is still "dependency-light":** the brief forbids *hard deps the
    user must install*; a file shipped in the skill is not that. Node has no
    built-in JS AST, so a real AST means either bundling a parser or asking the user
    to install one — vendoring keeps the "nothing extra to install" guarantee. Cost:
    the skill grew from ~204K to ~448K (acorn is ~245K unminified). Acceptable for a
    real AST; the token engine remains the safety net.
  - Glob expansion uses `fs.readdirSync` (no extra packages).
- **Model gates: Python `urllib`** (no `requests` dependency). The only network
  access in the whole skill, and only to the configured endpoint.

## Design decisions

- **Enforcement in scripts, procedure in the skill.** Every rule that must hold is
  a gate with a real exit code (`0/1/2/3/≥10`). SKILL.md carries no enforceable
  rule as prose.
- **One contract, swappable tools.** `gates.config` = orchestration
  (enabled/tier/command/endpoint); `policy.json` = behavior (thresholds, banned
  patterns, file conventions). `--config` is an orchestration extra the runner
  passes; the base three-flag contract (`--changed --policy [--context]`) is what a
  standalone gate needs.
- **BYO gates ship no tool.** `mutation`/`coverage`/`lint` are config pointing at a
  project command; the one shipped helper (`adapter`) turns any pass/fail exit code
  into a contract verdict. No mutation/coverage/lint/model-proxy/language is
  hardcoded anywhere (only the JS/TS reference `intent-gate`).
- **Everything heavy/BYO/model is disabled by default** in `gates.config.example`,
  so a fresh install runs immediately.
- **Loop-back routing is data, not prose.** The runner tags each escalation
  `route: code|tests|spec`, so the host sends code failures to the Author and test
  failures to the Judge — the Author never edits the tests that grade it.
- **Separation is enforceable.** Procedural separation (subagents/fresh contexts)
  is the default; `separation-gate` + a provenance manifest makes Author≠Judge a
  checked fact. Manifest parsing is dependency-free (JSON, or a tiny documented
  YAML subset — no PyYAML).

## Extensions beyond the target tree

- `agents/fofo-judge.md`, `agents/fofo-reviewer.md` — ready Claude Code subagent
  definitions for concrete role separation (the brief asked to "implement the
  Claude Code path concretely").
- `examples/sample-feature/smoke.sh` + `fixtures/` (incl. a local
  `mock_model.py`) — the runnable acceptance test.

## Smoke test

`examples/sample-feature/` is a slugify feature with two requirements and
intentionally weak tests. `smoke.sh` works on a temp copy (never mutates the
committed sample) and proves all 7 acceptance criteria. The model gate is
exercised against a **local mock endpoint** (`fixtures/mock_model.py`) so the full
HTTP→parse→verdict path runs with no real API key and no external network.

Run:

```
$ cd examples/sample-feature && bash smoke.sh
```

Result: **ALL CHECKS PASSED** (exit 0). Mapping to the acceptance criteria:

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Fresh install: runner with language-agnostic gates → valid aggregate JSON | ✅ exit 0, schema-valid |
| 2 | `trace-gate` fails on untraced requirement, passes when traced | ✅ fail→pass |
| 3 | `redgreen-gate` red-before / green-after | ✅ RED(stub)→GREEN(impl) |
| 4 | `intent-gate` flags assertion-free JS test, passes with real assertion | ✅ fail→pass |
| 5 | `semantic-test-judge` returns a contract verdict from the model endpoint | ✅ verdict via mock |
| 6 | `separation-gate` fails when one context authored tests+code | ✅ fail→pass |
| 7 | Every gate honors exit codes; runner aggregates + escalates with routing | ✅ overall fail, `intent-gate→tests` |

### Captured run

```text

=== CHECK 1: fresh install — runner with only language-agnostic gates -> valid aggregate JSON ===
[spec-lint] tier 0 -> pass : 2 requirement(s), all with IDs + acceptance criteria
[trace-gate] tier 0 -> pass : 2/2 requirements traced (intents=2, tagged=2)
[redgreen-gate] tier 0 -> pass : suite is GREEN as expected
[intent-gate] tier 0 -> pass : 1 test file(s): all tests assert intent [engine ast:1]
[separation-gate] tier 0 -> pass : 1 unit(s): tests and code authored by separate contexts

OVERALL: pass (exit 0) — 5 gate(s) ran, 0 escalation(s)
{
  "overall_status": "pass",
  "overall_exit": 0,
  "stopped_early": null,
  "ran": 5,
  "gates": [
    {
      "gate": "spec-lint",
      "tier": 0,
      "status": "pass",
      "summary": "2 requirement(s), all with IDs + acceptance criteria",
      "findings": [],
      "confidence": 1.0,
      "exit": 0,
      "route": "spec"
    },
    {
      "gate": "trace-gate",
      "tier": 0,
      "status": "pass",
      "summary": "2/2 requirements traced (intents=2, tagged=2)",
      "findings": [],
      "confidence": 1.0,
      "exit": 0,
      "route": "tests"
    },
    {
      "gate": "redgreen-gate",
      "tier": 0,
      "status": "pass",
      "summary": "suite is GREEN as expected",
      "findings": [],
      "confidence": 1.0,
      "exit": 0,
      "route": "code"
    },
    {
      "gate": "intent-gate",
      "tier": 0,
      "status": "pass",
      "summary": "1 test file(s): all tests assert intent [engine ast:1]",
      "findings": [],
      "confidence": 0.9,
      "exit": 0,
      "route": "tests"
    },
    {
      "gate": "separation-gate",
      "tier": 0,
      "status": "pass",
      "summary": "1 unit(s): tests and code authored by separate contexts",
      "findings": [],
      "confidence": 1.0,
      "exit": 0,
      "route": "tests"
    }
  ],
  "escalation": []
}
  aggregate JSON valid; gates ran: ['spec-lint', 'trace-gate', 'redgreen-gate', 'intent-gate', 'separation-gate']
  ✅ runner passes on the good sample (exit 0 as expected)

=== CHECK 2: trace-gate fails on an untraced requirement, passes once traced ===
{"gate": "trace-gate", "tier": 0, "status": "fail", "summary": "1/3 requirement(s) untraced", "findings": [{"severity": "high", "location": "REQUIREMENTS.md", "detail": "Requirement 'REQ-003' has no test intent and no tagged test."}], "confidence": 1.0}
  ✅ untraced REQ-003 -> fail (exit 1 as expected)
{"gate": "trace-gate", "tier": 0, "status": "pass", "summary": "2/2 requirements traced (intents=2, tagged=2)", "findings": [], "confidence": 1.0}
  ✅ all requirements traced -> pass (exit 0 as expected)

=== CHECK 3: redgreen-gate is red before implementation, green after ===
{"gate": "redgreen-gate", "tier": 0, "status": "pass", "summary": "suite is RED as expected (pre-implementation)", "findings": [], "confidence": 1.0}
  ✅ stub implementation -> RED as expected (exit 0 as expected)
{"gate": "redgreen-gate", "tier": 0, "status": "pass", "summary": "suite is GREEN as expected", "findings": [], "confidence": 1.0}
  ✅ real implementation -> GREEN as expected (exit 0 as expected)

=== CHECK 4: intent-gate flags assertion-free/trivial tests, passes real ones ===
{"gate":"intent-gate","tier":0,"status":"fail","summary":"2 test(s) assert no intent (of 2 issue(s)) [engine ast:1]","findings":[{"severity":"high","location":"fixtures/weak.test.js:9","detail":"Test \"REQ-001 builds a slug\" is assertion-free — asserts no behavior/intent."},{"severity":"high","location":"fixtures/weak.test.js:14","detail":"Test \"REQ-002 sanity\" is trivial — asserts no behavior/intent."}],"confidence":0.95}
  ✅ weak tests -> fail (exit 1 as expected)
{"gate":"intent-gate","tier":0,"status":"pass","summary":"1 test file(s): all tests assert intent [engine ast:1]","findings":[],"confidence":0.9}
  ✅ real tests -> pass (exit 0 as expected)

=== CHECK 5: semantic-test-judge returns a contract verdict via the model endpoint ===
{"gate": "semantic-test-judge", "tier": 1, "status": "fail", "summary": "2 tests touch lines without asserting requirement intent", "findings": [{"severity": "high", "location": "REQ-001 builds a slug", "detail": "Does not assert requirement intent: calls slugify() but never checks the returned value (conf 0.90)"}, {"severity": "high", "location": "REQ-002 sanity", "detail": "Does not assert requirement intent: asserts 1===1, a tautology unrelated to the requirement (conf 0.88)"}], "confidence": 0.89}
  ✅ model judge returns a verdict (fail: tests don't assert intent) (exit 1 as expected)

=== CHECK 6: separation-gate fails when one context authored both tests and code ===
{"gate": "separation-gate", "tier": 0, "status": "fail", "summary": "1 unit(s) violate Author!=Judge separation", "findings": [{"severity": "high", "location": "slugify", "detail": "Same context 'solo-ctx-2026-06-20' authored both tests and code for unit 'slugify'."}], "confidence": 1.0}
  ✅ same context for tests+code -> fail (exit 1 as expected)
{"gate": "separation-gate", "tier": 0, "status": "pass", "summary": "1 unit(s): tests and code authored by separate contexts", "findings": [], "confidence": 1.0}
  ✅ separate contexts -> pass (exit 0 as expected)

=== CHECK 7: every gate honors exit codes; runner aggregates + routes escalations ===
[spec-lint] tier 0 -> pass : 2 requirement(s), all with IDs + acceptance criteria
[trace-gate] tier 0 -> pass : 2/2 requirements traced (intents=2, tagged=2)
[redgreen-gate] tier 0 -> pass : suite is GREEN as expected
[intent-gate] tier 0 -> fail : 2 test(s) assert no intent (of 2 issue(s)) [engine ast:2]

OVERALL: fail (exit 1) — 4 gate(s) ran, 1 escalation(s)
{
  "overall_status": "fail",
  "overall_exit": 1,
  "stopped_early": "fail",
  "ran": 4,
  "gates": [
    {
      "gate": "spec-lint",
      "tier": 0,
      "status": "pass",
      "summary": "2 requirement(s), all with IDs + acceptance criteria",
      "findings": [],
      "confidence": 1.0,
      "exit": 0,
      "route": "spec"
    },
    {
      "gate": "trace-gate",
      "tier": 0,
      "status": "pass",
      "summary": "2/2 requirements traced (intents=2, tagged=2)",
      "findings": [],
      "confidence": 1.0,
      "exit": 0,
      "route": "tests"
    },
    {
      "gate": "redgreen-gate",
      "tier": 0,
      "status": "pass",
      "summary": "suite is GREEN as expected",
      "findings": [],
      "confidence": 1.0,
      "exit": 0,
      "route": "code"
    },
    {
      "gate": "intent-gate",
      "tier": 0,
      "status": "fail",
      "summary": "2 test(s) assert no intent (of 2 issue(s)) [engine ast:2]",
      "findings": [
        {
          "severity": "high",
          "location": "test/weak.test.js:9",
          "detail": "Test \"REQ-001 builds a slug\" is assertion-free \u2014 asserts no behavior/intent."
        },
        {
          "severity": "high",
          "location": "test/weak.test.js:14",
          "detail": "Test \"REQ-002 sanity\" is trivial \u2014 asserts no behavior/intent."
        }
      ],
      "confidence": 0.95,
      "exit": 1,
      "route": "tests"
    }
  ],
  "escalation": [
    {
      "gate": "intent-gate",
      "tier": 0,
      "status": "fail",
      "route": "tests",
      "waived": false,
      "summary": "2 test(s) assert no intent (of 2 issue(s)) [engine ast:2]",
      "confidence": 0.95,
      "findings": [
        {
          "severity": "high",
          "location": "test/weak.test.js:9",
          "detail": "Test \"REQ-001 builds a slug\" is assertion-free \u2014 asserts no behavior/intent."
        },
        {
          "severity": "high",
          "location": "test/weak.test.js:14",
          "detail": "Test \"REQ-002 sanity\" is trivial \u2014 asserts no behavior/intent."
        }
      ]
    }
  ]
}
  overall: fail exit 1
  escalations routed: [('intent-gate', 'tests')]
smoke.sh: line 98: 71050 Terminated: 15          python3 fixtures/mock_model.py "$PORT" > /tmp/fofo_mock.out 2>&1
  ✅ runner reports fail/escalate on a tainted suite (exit 1 as expected)

=== RESULT ===
ALL CHECKS PASSED
```
