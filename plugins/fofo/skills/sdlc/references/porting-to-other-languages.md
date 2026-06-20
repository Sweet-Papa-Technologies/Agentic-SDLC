# Porting to other languages

The loop is stack-agnostic by contract. Most gates already are; two places are
language-aware and this is how you adapt them.

## What is already language-agnostic

- **`spec-lint`, `trace-gate`, `separation-gate`** work on Markdown/YAML/JSON and a
  tag convention. Nothing to port — just set `id_pattern` / file names in
  `policy.json` if your conventions differ.
- **`redgreen-gate`** runs whatever `policy.gates.redgreen-gate.test_command` is.
  Point it at `pytest`, `go test`, `cargo test`, `mvn test`, `npm test` — anything
  that exits non-zero on failure.

## intent-gate: bring your own analyzer

The kept `intent-gate` understands **JS/TS**. It parses JS with a **real AST**
(acorn, vendored in `scripts/vendor/acorn.js` — ships with the skill, nothing to
install) and automatically falls back to its built-in token analyzer for files
acorn can't parse (TypeScript type syntax, JSX). For full TS-type fidelity you can
point it at an `acorn-typescript`/`typescript`-backed analyzer instead — same
contract.

To check test quality in another language, write an analyzer that emits the same
contract JSON and point `gates.config` at it via `command` instead of the kept
`script`:

```json
{ "name": "intent-gate", "tier": 0, "enabled": true,
  "command": ["python3", "tools/py_intent_gate.py"] }
```

The runner appends `--changed`, `--policy`, `--context`, `--config`. Your analyzer
must:

1. Parse the changed test files (use your language's real AST — `ast` for Python,
   `go/parser` for Go, `syn` for Rust, etc.).
2. For each test, classify it the way the JS/TS reference does:
   - **assertion-free** — no assertion in the body.
   - **trivial** — only trivially-true assertions (`assert True`, `assertEqual(1, 1)`).
   - **snapshot-only** — only snapshot/golden assertions.
   - **banned mock** — a mock/stub API the policy forbids.
3. Emit one JSON object: `{gate, tier, status, summary, findings[], confidence}`
   with exit `0/1/2/3` (see [gate-contract.md](gate-contract.md)).

A minimal Python skeleton:

```python
import ast, json, sys
# parse --changed, --policy; for each test function, walk the AST and look for
# `assert` / framework asserts; classify; then:
print(json.dumps({"gate":"intent-gate","tier":0,"status":status,
                  "summary":summary,"findings":findings,"confidence":conf}))
sys.exit({"pass":0,"fail":1,"escalate":2,"skip":3}[status])
```

The JS/TS reference (`scripts/intent-gate`) is a worked example of the same shape.

## mutation / coverage / lint: bring your own command

These were never language-specific in this skill — they are config pointing at a
project tool. Two ways to conform:

- The tool already emits a JSON report → wrap it with a few lines that translate
  its report into the contract.
- The tool is plain pass/fail → wrap with the kept `adapter`:

  ```json
  { "name": "coverage", "tier": 0, "enabled": true,
    "command": ["./scripts/adapter", "--name", "coverage", "--tier", "0", "--",
                "pytest", "--cov", "--cov-fail-under=80"] }
  ```

## Model gates

`semantic-test-judge` and `fresh-eyes-review` are language-neutral — they read text
and call the configured endpoint. No porting needed; they work on any source.
