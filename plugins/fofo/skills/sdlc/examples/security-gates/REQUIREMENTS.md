# secret-scan gate — requirements

A new kept, language-agnostic, Python-3-stdlib-only Tier-0 gate for the FoFo
Agentic SDLC. It obeys the standard gate contract (see
`references/gate-contract.md`): invoked with `--changed --policy [--context]
[--config]`, prints exactly one JSON verdict to stdout, and exits
`0` pass / `1` fail / `2` escalate / `3` skip / `>=10` internal error.

## secret-scan — deterministic hard-coded-secret detector

### REQ-001: Detect high-severity secrets in changed files
The gate scans every file named in `--changed` for hard-coded credentials using
deterministic patterns (AWS access key IDs matching `AKIA[0-9A-Z]{16}`, and PEM
private-key headers `-----BEGIN ... PRIVATE KEY-----`). A match is reported as a
`high`-severity finding whose `location` is `file:line`.
Acceptance: scanning a file that contains `AKIA` followed by 16 uppercase
alphanumerics exits `1` (fail) with at least one `high`-severity finding whose
location names that file and the matching line number.

### REQ-002: Pass cleanly when no secrets are present
A change that contains no secret material must not block the loop.
Acceptance: scanning a file with ordinary source code and no secret patterns
exits `0` (pass) with an empty `findings` array.

### REQ-003: Generic secret assignments escalate rather than hard-fail
An assignment whose identifier looks secret-bearing (e.g. `api_key`, `apikey`,
`secret`, `token`, `password`, `passwd`, `access_key`) to a quoted literal at
least `min_token_length` characters long is a likely-but-uncertain leak. By
default it is reported as a `med`-severity finding and the gate escalates.
Acceptance: scanning a file whose only secret-like content is
`api_key = "<24+ char quoted string>"` (and no high-severity pattern) exits `2`
(escalate) with a `med`-severity finding for that line, and `min_token_length`
is configurable under `policy.gates.secret-scan`.

### REQ-004: Allowlisted lines are ignored
Known-safe placeholders (documentation examples, test fixtures) must be
suppressible without disabling the gate.
Acceptance: when `policy.gates.secret-scan.allowlist` contains a regex that
matches a line, a secret on that line produces no finding; a file whose only
secret is allowlisted exits `0` (pass).

### REQ-005: Skip when there is nothing to scan
Acceptance: invoking the gate with no existing files in `--changed` exits `3`
(skip) and still prints one contract-shaped JSON verdict.

### REQ-006: Detect secret-looking assignments across common formats
Real configs express the same secret many ways. Beyond the bare `key = "value"`
form, the gate must also catch quoted-key JSON (`"api_key": "value"`) and
unquoted environment/YAML scalars (`API_KEY=value`), still honoring
`min_token_length`.
Acceptance: a file whose only secret-like content is a quoted-key JSON entry
`"api_key": "<24+ char value>"` exits `2` (escalate) with a `med`-severity
finding for that line, and a file containing only `API_KEY=<24+ char value>`
(no quotes) likewise exits `2` with a `med`-severity finding.

### REQ-007: A malformed allowlist regex never crashes the gate
Gate configuration is user-supplied; a typo in it must not hard-stop the whole
pipeline. An invalid regex in `policy.gates.secret-scan.allowlist` is skipped,
scanning continues, and the gate returns a normal contract verdict.
Acceptance: with `allowlist` containing an un-compilable regex (e.g. `"[invalid("`)
while scanning a file with a hard-coded AWS key, the gate exits `1` (fail, the
key is still detected) — never `>=10` (internal error).
