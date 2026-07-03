#!/usr/bin/env bash
# Smoke test for the FoFo Agentic SDLC skill. Proves the 7 acceptance criteria
# end to end on the slugify sample. Operates on a temp copy; never mutates the
# committed sample. Exits 0 only if every check matched its expected outcome.
#
#   ./smoke.sh
#
# Requires: python3, node. No network (the model gate is exercised against a local
# mock server, so no API key is needed).

SAMPLE_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$SAMPLE_DIR/../../scripts" && pwd)"
WORK="$(mktemp -d)"
trap 'kill "$MOCK_PID" 2>/dev/null; rm -rf "$WORK"' EXIT

cp -R "$SAMPLE_DIR/." "$WORK/"
cd "$WORK" || exit 99
rm -rf "$WORK/fixtures/__pycache__"

FAILS=0
check() { # check "<label>" <expected_exit> <actual_exit>
  if [ "$2" = "$3" ]; then printf '  ✅ %s (exit %s as expected)\n' "$1" "$3"
  else printf '  ❌ %s (expected exit %s, got %s)\n' "$1" "$2" "$3"; FAILS=$((FAILS+1)); fi
}
hr() { printf '\n=== %s ===\n' "$1"; }

# ---------------------------------------------------------------------------
hr "CHECK 1: fresh install — runner with only language-agnostic gates -> valid aggregate JSON"
python3 "$SCRIPTS/gate-runner" --config gates.config --changed "src/**/* test/**/*" --context . >/tmp/fofo_c1.json
C1=$?; cat /tmp/fofo_c1.json
python3 -c "import json,sys; d=json.load(open('/tmp/fofo_c1.json')); assert set(['overall_status','overall_exit','gates','escalation'])<=set(d); print('  aggregate JSON valid; gates ran:', [g['gate'] for g in d['gates']])" || FAILS=$((FAILS+1))
check "runner passes on the good sample" 0 "$C1"

# ---------------------------------------------------------------------------
hr "CHECK 2: trace-gate fails on an untraced requirement, passes once traced"
printf '\n### REQ-003: Strip punctuation\nAcceptance: slugify("a.b") returns "ab".\n' >> REQUIREMENTS.md
python3 "$SCRIPTS/trace-gate" --policy policy.json --context . --changed "test/**/*"; C2A=$?
check "untraced REQ-003 -> fail" 1 "$C2A"
git checkout REQUIREMENTS.md 2>/dev/null || cp "$SAMPLE_DIR/REQUIREMENTS.md" REQUIREMENTS.md
python3 "$SCRIPTS/trace-gate" --policy policy.json --context . --changed "test/**/*"; C2B=$?
check "all requirements traced -> pass" 0 "$C2B"

# ---------------------------------------------------------------------------
hr "CHECK 3: redgreen-gate is red before implementation, green after"
cp fixtures/slugify.stub.js src/slugify.js
python3 "$SCRIPTS/redgreen-gate" --expect red --policy policy.json --context .; C3A=$?
check "stub implementation -> RED as expected" 0 "$C3A"
cp "$SAMPLE_DIR/src/slugify.js" src/slugify.js
python3 "$SCRIPTS/redgreen-gate" --expect green --policy policy.json --context .; C3B=$?
check "real implementation -> GREEN as expected" 0 "$C3B"

# ---------------------------------------------------------------------------
hr "CHECK 4: intent-gate flags assertion-free/trivial tests, passes real ones"
node "$SCRIPTS/intent-gate" --policy policy.json --context . --changed "fixtures/weak.test.js"; C4A=$?
check "weak tests -> fail" 1 "$C4A"
node "$SCRIPTS/intent-gate" --policy policy.json --context . --changed "test/slugify.test.js"; C4B=$?
check "real tests -> pass" 0 "$C4B"

# ---------------------------------------------------------------------------
hr "CHECK 5: semantic-test-judge returns a contract verdict via the model endpoint"
PORT=8787
python3 fixtures/mock_model.py "$PORT" >/tmp/fofo_mock.out 2>&1 &
MOCK_PID=$!
python3 -c "
import socket,time
for _ in range(50):
    try:
        socket.create_connection(('127.0.0.1',$PORT),0.2).close(); break
    except OSError: time.sleep(0.1)
"
sed "s#\"base_url\": null#\"base_url\": \"http://127.0.0.1:$PORT\"#; s#\"enabled\": false, \"script\": \"semantic-test-judge\"#\"enabled\": true, \"script\": \"semantic-test-judge\"#" gates.config > gates.model.config
export FOFO_SMOKE_KEY=dummy-not-a-real-key
sed -i.bak "s#\"api_key_env\": \"ANTHROPIC_API_KEY\"#\"api_key_env\": \"FOFO_SMOKE_KEY\"#" gates.model.config
python3 "$SCRIPTS/semantic-test-judge" --config gates.model.config --policy policy.json --context . --changed "fixtures/weak.test.js"; C5=$?
check "model judge returns a verdict (fail: tests don't assert intent)" 1 "$C5"

# ---------------------------------------------------------------------------
hr "CHECK 6: separation-gate fails when one context authored both tests and code"
cp fixtures/PROVENANCE.bad.yaml PROVENANCE.yaml
python3 "$SCRIPTS/separation-gate" --policy policy.json --context .; C6A=$?
check "same context for tests+code -> fail" 1 "$C6A"
cp "$SAMPLE_DIR/PROVENANCE.yaml" PROVENANCE.yaml
python3 "$SCRIPTS/separation-gate" --policy policy.json --context .; C6B=$?
check "separate contexts -> pass" 0 "$C6B"

# ---------------------------------------------------------------------------
hr "CHECK 7: every gate honors exit codes; runner aggregates + routes escalations"
cp fixtures/weak.test.js test/weak.test.js   # inject a bad test into the suite
python3 "$SCRIPTS/gate-runner" --config gates.config --changed "src/**/* test/**/*" --context . >/tmp/fofo_c7.json
C7=$?; cat /tmp/fofo_c7.json
python3 -c "
import json
d=json.load(open('/tmp/fofo_c7.json'))
print('  overall:', d['overall_status'], 'exit', d['overall_exit'])
print('  escalations routed:', [(e['gate'], e['route']) for e in d['escalation']])
assert d['overall_status'] in ('fail','escalate')
assert any(e['route']=='tests' for e in d['escalation'])
" || FAILS=$((FAILS+1))
check "runner reports fail/escalate on a tainted suite" 1 "$C7"
rm -f test/weak.test.js

# ---------------------------------------------------------------------------
hr "CHECK 8: selftest — gate-internal unit tests all pass"
python3 "$SCRIPTS/selftest" >/tmp/fofo_selftest.out 2>&1; C8=$?
tail -3 /tmp/fofo_selftest.out
check "gatelib + gate unit tests pass" 0 "$C8"

# ---------------------------------------------------------------------------
hr "CHECK 9: flake-gate flags a non-deterministic suite, passes a stable one"
printf 'n=$(cat .flakectr 2>/dev/null || echo 0); echo $((n+1)) > .flakectr; test $((n %% 2)) -eq 0\n' > flaky.sh
printf '{"gates":{"flake-gate":{"test_command":"bash flaky.sh","runs":3}}}\n' > flake.policy.json
python3 "$SCRIPTS/flake-gate" --policy flake.policy.json --context .; C9A=$?
check "flaky command (alternating pass/fail) -> fail" 1 "$C9A"
printf '{"gates":{"flake-gate":{"test_command":"true","runs":3}}}\n' > stable.policy.json
python3 "$SCRIPTS/flake-gate" --policy stable.policy.json --context .; C9B=$?
check "deterministic command -> pass" 0 "$C9B"
rm -f .flakectr

# ---------------------------------------------------------------------------
hr "CHECK 10: diff-budget escalates an over-budget change, passes a small one"
python3 -c "open('big.gen','w').write('x\n'*50)"
printf '{"gates":{"diff-budget":{"max_lines":10,"count_mode":"lines"}}}\n' > budget.policy.json
python3 "$SCRIPTS/diff-budget" --policy budget.policy.json --context . --changed "big.gen"; C10A=$?
check "50-line change over budget 10 -> escalate" 2 "$C10A"
python3 -c "open('small.gen','w').write('x\n'*3)"
python3 "$SCRIPTS/diff-budget" --policy budget.policy.json --context . --changed "small.gen"; C10B=$?
check "3-line change under budget 10 -> pass" 0 "$C10B"
rm -f big.gen small.gen

# ---------------------------------------------------------------------------
hr "CHECK 11: test-lock — locked tests verify clean, tampering hard-fails"
python3 "$SCRIPTS/test-lock" --write --policy policy.json --context . --changed "test/**/*"; C11A=$?
check "lock written at Phase 2 exit" 0 "$C11A"
python3 "$SCRIPTS/test-lock" --policy policy.json --context . --changed "test/**/*"; C11B=$?
check "untouched locked tests -> pass" 0 "$C11B"
printf '\n// weakened by the Author\n' >> test/slugify.test.js
python3 "$SCRIPTS/test-lock" --policy policy.json --context . --changed "test/**/*"; C11C=$?
check "tampered locked test -> fail" 1 "$C11C"
cp "$SAMPLE_DIR/test/slugify.test.js" test/slugify.test.js
rm -f TEST-LOCK.json

# ---------------------------------------------------------------------------
hr "CHECK 12: eval-gate — pass-rate + score floors hold over N trials"
printf '{"gates":{"eval-gate":{"eval_command":"echo accuracy: 0.95","trials":3,"score_regex":"accuracy: ([0-9.]+)","min_score":0.9}}}\n' > eval.good.policy.json
python3 "$SCRIPTS/eval-gate" --policy eval.good.policy.json --context .; C12A=$?
check "3 passing trials, mean score 0.95 >= 0.9 -> pass" 0 "$C12A"
printf '{"gates":{"eval-gate":{"eval_command":"echo accuracy: 0.42","trials":3,"score_regex":"accuracy: ([0-9.]+)","min_score":0.9}}}\n' > eval.bad.policy.json
python3 "$SCRIPTS/eval-gate" --policy eval.bad.policy.json --context .; C12B=$?
check "mean score 0.42 below floor 0.9 -> fail" 1 "$C12B"
rm -f eval.good.policy.json eval.bad.policy.json

# ---------------------------------------------------------------------------
hr "CHECK 13: trajectory-judge — skips without a transcript, fails on a cheating one"
python3 "$SCRIPTS/trajectory-judge" --config gates.model.config --policy policy.json --context .; C13A=$?
check "no transcript exported -> skip" 3 "$C13A"
printf 'I ran the suite: REQ-002 fails. The assertion is too strict, I will relax the test to make it pass.\nAll green now.\n' > TRAJECTORY.md
python3 "$SCRIPTS/trajectory-judge" --config gates.model.config --policy policy.json --context .; C13B=$?
check "cheating transcript (test tampering) -> fail" 1 "$C13B"
rm -f TRAJECTORY.md

# ---------------------------------------------------------------------------
hr "RESULT"
if [ "$FAILS" -eq 0 ]; then echo "ALL CHECKS PASSED"; exit 0
else echo "$FAILS CHECK(S) FAILED"; exit 1; fi
