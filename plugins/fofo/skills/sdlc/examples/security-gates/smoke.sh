#!/usr/bin/env bash
# Smoke test for the secret-scan gate and its FoFo dogfood loop. Proves the gate's
# acceptance criteria (REQ-001..REQ-005) end to end, and that the whole test-first
# loop is green on this example. Read-only checks run in place (no bytecode written,
# so the committed tree is not mutated); planted-secret fixtures live in a temp dir.
# Exits 0 only if every check matched its expected outcome.
#
#   ./smoke.sh
#
# Requires: python3. No network. Secret fixtures are assembled at runtime so this
# script itself contains no credential-shaped literal.

export PYTHONDONTWRITEBYTECODE=1
SAMPLE_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$SAMPLE_DIR/../../scripts" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
find "$SAMPLE_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null

FAILS=0
check() { # check "<label>" <expected_exit> <actual_exit>
  if [ "$2" = "$3" ]; then printf '  ✅ %s (exit %s as expected)\n' "$1" "$3"
  else printf '  ❌ %s (expected exit %s, got %s)\n' "$1" "$2" "$3"; FAILS=$((FAILS+1)); fi
}
hr() { printf '\n=== %s ===\n' "$1"; }
scan() { python3 "$SCRIPTS/secret-scan" --context "$WORK" --changed "$1" "${@:2}"; }

# Secret material built at runtime — never a literal in this file.
AWS_KEY="AKIA$(printf 'A%.0s' $(seq 1 16))"
PEM_HEADER="$(printf -- '-%.0s' $(seq 1 5))BEGIN RSA PRIVATE KEY$(printf -- '-%.0s' $(seq 1 5))"
LONG_LITERAL="$(printf 'x%.0s' $(seq 1 30))"
POLICY="$WORK/policy.json"
printf '{"gates":{"secret-scan":{"min_token_length":16,"allowlist":[],"fail_on":["high"]}}}' > "$POLICY"
mkdir -p "$WORK/planted"

# ---------------------------------------------------------------------------
hr "CHECK 1: the FoFo loop is green on this example (spec-lint, trace, redgreen, runner)"
( cd "$SAMPLE_DIR" && python3 "$SCRIPTS/gate-runner" --config gates.config --changed "test/**/*" --context . ) >/tmp/secscan_c1.json 2>/dev/null
C1=$?; cat /tmp/secscan_c1.json
python3 -c "import json; d=json.load(open('/tmp/secscan_c1.json')); assert set(['overall_status','overall_exit','gates','escalation'])<=set(d); assert d['overall_status']=='pass'; print('  loop green; gates ran:', [g['gate'] for g in d['gates']])" || FAILS=$((FAILS+1))
check "runner passes the dogfood loop" 0 "$C1"

# ---------------------------------------------------------------------------
hr "CHECK 2: REQ-001 — a planted AWS access key id is a high-severity hard fail"
printf 'import os\nAWS_KEY = "%s"\n' "$AWS_KEY" > "$WORK/planted/leak.py"
scan "planted/leak.py" --policy "$POLICY" >/tmp/secscan_c2.json; C2=$?
cat /tmp/secscan_c2.json
python3 -c "import json; d=json.load(open('/tmp/secscan_c2.json')); assert any(f['severity']=='high' and 'leak.py' in f['location'] for f in d['findings']), 'expected a high finding naming leak.py'; print('  high finding present')" || FAILS=$((FAILS+1))
check "AWS key -> hard fail" 1 "$C2"

# ---------------------------------------------------------------------------
hr "CHECK 3: REQ-001 — a planted PEM private-key header is a high-severity hard fail"
printf 'intro\n%s\n' "$PEM_HEADER" > "$WORK/planted/id_rsa"
scan "planted/id_rsa" --policy "$POLICY" >/dev/null; C3=$?
check "PEM private-key header -> hard fail" 1 "$C3"

# ---------------------------------------------------------------------------
hr "CHECK 4: REQ-002 — ordinary source with no secrets passes with empty findings"
printf 'def add(a, b):\n    return a + b\n' > "$WORK/planted/clean.py"
scan "planted/clean.py" --policy "$POLICY" >/tmp/secscan_c4.json; C4=$?
python3 -c "import json; d=json.load(open('/tmp/secscan_c4.json')); assert d['findings']==[], 'clean pass must have empty findings'; print('  clean, empty findings')" || FAILS=$((FAILS+1))
check "clean code -> pass" 0 "$C4"

# ---------------------------------------------------------------------------
hr "CHECK 5: REQ-003 — a secret-looking assignment escalates (not a hard fail)"
printf 'name = "svc"\napi_key = "%s"\n' "$LONG_LITERAL" > "$WORK/planted/settings.py"
scan "planted/settings.py" --policy "$POLICY" >/tmp/secscan_c5.json; C5=$?
python3 -c "import json; d=json.load(open('/tmp/secscan_c5.json')); assert any(f['severity']=='med' for f in d['findings']), 'expected a med finding'; print('  med finding present')" || FAILS=$((FAILS+1))
check "generic secret assignment -> escalate" 2 "$C5"

# ---------------------------------------------------------------------------
hr "CHECK 6: REQ-004 — an allowlisted line suppresses the secret"
printf 'AWS_KEY = "%s"  # example-placeholder\n' "$AWS_KEY" > "$WORK/planted/doc.py"
printf '{"gates":{"secret-scan":{"allowlist":["example-placeholder"]}}}' > "$WORK/policy.allow.json"
scan "planted/doc.py" --policy "$WORK/policy.allow.json" >/dev/null; C6=$?
check "allowlisted secret -> pass" 0 "$C6"

# ---------------------------------------------------------------------------
hr "CHECK 7: REQ-005 — nothing to scan skips with a contract-shaped verdict"
scan "planted/nope.py" --policy "$POLICY" >/tmp/secscan_c7.json; C7=$?
python3 -c "import json; d=json.load(open('/tmp/secscan_c7.json')); assert set(['gate','tier','status','summary','findings','confidence'])<=set(d) and d['status']=='skip'; print('  skip verdict well-formed')" || FAILS=$((FAILS+1))
check "no files to scan -> skip" 3 "$C7"

# ---------------------------------------------------------------------------
hr "CHECK 8: the Judge's test suite (REQ-001..005) is green against the implementation"
( cd "$SAMPLE_DIR" && python3 -m unittest discover -s test -p 'test_*.py' ) >/tmp/secscan_c8.out 2>&1; C8=$?
tail -3 /tmp/secscan_c8.out
check "Judge's tests pass" 0 "$C8"

find "$SAMPLE_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null

# ---------------------------------------------------------------------------
hr "RESULT"
if [ "$FAILS" -eq 0 ]; then echo "ALL CHECKS PASSED"; exit 0
else echo "$FAILS CHECK(S) FAILED"; exit 1; fi
