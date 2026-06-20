# Gate Contract

Every gate — kept default or bring-your-own — obeys one uniform contract so the
runner can treat them interchangeably and any tool can fulfill any gate.

## Invocation

```
<gate-script> --changed <path-or-glob-list> --policy <policy.json> [--context <dir>] [--config <gates.config>]
```

- `--changed` — files under judgment. Repeatable and/or comma/space separated.
  Globs (`src/**/*.ts`) and directories are expanded. May be empty.
- `--policy` — path to `policy.json`. Thresholds, banned patterns, per-gate
  options. A gate reads its own options from `policy.gates.<gate-name>`.
- `--context` — project root the gate resolves relative paths against. Defaults `.`.
- `--config` — path to `gates.config`. The base contract is the three flags
  above; `--config` is an **orchestration extra** the runner always passes so
  model gates can find the endpoint and BYO gates their command. Standalone gates
  fall back to `./gates.config` if present.

## stdout — exactly one JSON object

```json
{
  "gate": "mutation",
  "tier": 0,
  "status": "pass | fail | escalate | skip",
  "summary": "one human-readable line",
  "findings": [
    { "severity": "low|med|high", "location": "file:line", "detail": "..." }
  ],
  "confidence": 0.0
}
```

Anything a gate writes to **stderr** is diagnostics and ignored by the runner.
Only the single stdout JSON object is parsed.

## Exit codes (authoritative — the runner trusts these over status text)

| code   | meaning            | runner behavior                                  |
|--------|--------------------|--------------------------------------------------|
| `0`    | pass               | continue                                         |
| `1`    | hard fail          | record; stop (fail-fast) unless marked waivable  |
| `2`    | escalate           | record; collect into escalation payload; continue|
| `3`    | skip/not-configured| non-blocking; continue                           |
| `>=10` | gate internal error| hard stop; surface the error                     |

`status` and the exit code must agree. If they disagree the runner trusts the
exit code and notes the mismatch.

## Writing a gate in any language

A conforming gate is any executable that:
1. Accepts the flags above (it may ignore ones it doesn't need).
2. Prints one JSON object matching the schema to stdout.
3. Exits with the matching code.

The kept Python gates use `scripts/gatelib.py` for this; `intent-gate` is Node and
implements the same contract directly. Neither is required — see
[porting-to-other-languages.md](porting-to-other-languages.md).

## Bring-your-own gates

`mutation`, `coverage`, and `lint` are not shipped as tools. In `gates.config`
they carry a `command` pointing at a project tool. Two ways to make a tool
conform:

- The tool already emits contract JSON (some mutation tools have a JSON report —
  wrap it with a tiny script you write).
- The tool is a plain pass/fail command: wrap it with `scripts/adapter`, which
  turns an exit code into a contract verdict:

  ```
  adapter --name lint --tier 0 -- eslint src/
  ```

No gate fetches arbitrary network URLs at runtime. The only network access is the
user-configured model endpoint used by `semantic-test-judge` and
`fresh-eyes-review`.
