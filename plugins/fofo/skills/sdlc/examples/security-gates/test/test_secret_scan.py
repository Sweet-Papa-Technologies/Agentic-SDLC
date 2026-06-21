"""Behavior tests for the secret-scan gate (REQ-001 .. REQ-005).

Asserted against the gate contract only: each test invokes the script as a black
box and checks BOTH the process exit code and a meaningful property of the parsed
JSON verdict. The implementation is not read.

Secret fixtures are assembled at runtime from pieces so the test source itself
contains no credential-shaped literal that would trip the gate we ship.
"""

import os
import tempfile
import unittest

from _util import (
    SECRET_SCAN,
    run_gate,
    write,
    write_policy,
    findings_for_file,
)


# --- secret material constructed at runtime (never a literal in source) ---

def fake_aws_key():
    # AKIA followed by 16 uppercase alphanumerics -> matches AKIA[0-9A-Z]{16}
    return "AKIA" + "A" * 16


def fake_pem_header():
    # Assemble the PEM private-key header from pieces.
    dashes = "-" * 5
    return dashes + "BEGIN RSA PRIVATE KEY" + dashes


class SecretScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _high(self, verdict):
        return [f for f in verdict.get("findings", []) if f.get("severity") == "high"]

    def _med(self, verdict):
        return [f for f in verdict.get("findings", []) if f.get("severity") == "med"]

    def test_aws_access_key_is_high_severity_fail(self):
        # @req:REQ-001 AWS access key id -> exit 1 + high finding at file:line.
        target = write(
            os.path.join(self.tmp, "config.py"),
            "import os\n"
            "AWS_KEY = '%s'\n"
            "value = 1\n" % fake_aws_key(),
        )
        policy = write_policy(self.tmp, "secret-scan", {})
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 1, "AWS key should hard-fail; stdout=%r" % raw)
        self.assertIsNotNone(verdict, "gate must print one JSON verdict")
        highs = self._high(verdict)
        self.assertTrue(highs, "expected at least one high-severity finding")
        matched = findings_for_file(verdict, "config.py")
        self.assertTrue(matched, "a finding must name config.py")
        # location must be file:line and point at line 2 (the key line).
        loc = matched[0]["location"]
        self.assertIn(":", loc, "location must be file:line")
        self.assertEqual(loc.rsplit(":", 1)[1], "2",
                         "location must name the matching line; got %r" % loc)

    def test_pem_private_key_header_is_high_severity_fail(self):
        # @req:REQ-001 PEM private-key header -> exit 1 + high finding at file:line.
        target = write(
            os.path.join(self.tmp, "key.pem"),
            "intro line\n"
            "%s\n" % fake_pem_header(),
        )
        policy = write_policy(self.tmp, "secret-scan", {})
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 1, "PEM header should hard-fail; stdout=%r" % raw)
        self.assertTrue(self._high(verdict), "expected a high-severity finding")
        matched = findings_for_file(verdict, "key.pem")
        self.assertTrue(matched, "a finding must name key.pem")
        self.assertEqual(matched[0]["location"].rsplit(":", 1)[1], "2",
                         "PEM header is on line 2")

    def test_clean_file_passes_with_no_findings(self):
        # @req:REQ-002 ordinary source, no secrets -> exit 0 + empty findings.
        target = write(
            os.path.join(self.tmp, "math.py"),
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "TOTAL = add(2, 3)\n",
        )
        policy = write_policy(self.tmp, "secret-scan", {})
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 0, "clean file should pass; stdout=%r" % raw)
        self.assertEqual(verdict.get("findings"), [],
                         "clean pass must have an empty findings array")

    def test_generic_secret_assignment_escalates_med(self):
        # @req:REQ-003 api_key = "<24+ chars>" with no high pattern -> exit 2 + med.
        literal = "x" * 30  # 30 chars, well over a 24 min_token_length
        target = write(
            os.path.join(self.tmp, "settings.py"),
            "name = 'service'\n"
            "api_key = \"%s\"\n" % literal,
        )
        policy = write_policy(self.tmp, "secret-scan", {"min_token_length": 24})
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 2, "generic secret should escalate; stdout=%r" % raw)
        meds = self._med(verdict)
        self.assertTrue(meds, "expected a med-severity finding")
        matched = [f for f in findings_for_file(verdict, "settings.py")
                   if f.get("severity") == "med"]
        self.assertTrue(matched, "med finding must name settings.py")
        self.assertEqual(matched[0]["location"].rsplit(":", 1)[1], "2",
                         "the api_key line is line 2")

    def test_min_token_length_below_threshold_passes(self):
        # @req:REQ-003 quoted literal shorter than min_token_length -> no finding.
        short = "y" * 8  # under the configured 24
        target = write(
            os.path.join(self.tmp, "settings.py"),
            "api_key = \"%s\"\n" % short,
        )
        policy = write_policy(self.tmp, "secret-scan", {"min_token_length": 24})
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 0,
                         "short literal is below min_token_length; stdout=%r" % raw)
        self.assertEqual(verdict.get("findings"), [],
                         "no finding for a sub-threshold literal")

    def test_allowlisted_secret_line_is_ignored(self):
        # @req:REQ-004 allowlist regex matching the line suppresses the secret.
        target = write(
            os.path.join(self.tmp, "example_doc.py"),
            "AWS_KEY = '%s'  # example-placeholder\n" % fake_aws_key(),
        )
        policy = write_policy(
            self.tmp, "secret-scan",
            {"allowlist": ["example-placeholder"]},
        )
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 0,
                         "allowlisted secret must not block; stdout=%r" % raw)
        self.assertEqual(verdict.get("findings"), [],
                         "allowlisted secret produces no finding")

    def test_no_existing_files_skips(self):
        # @req:REQ-005 no existing files in --changed -> exit 3 + contract verdict.
        missing = os.path.join(self.tmp, "does_not_exist.py")
        policy = write_policy(self.tmp, "secret-scan", {})
        code, verdict, raw = run_gate(SECRET_SCAN, missing, policy, self.tmp)

        self.assertEqual(code, 3, "nothing to scan should skip; stdout=%r" % raw)
        self.assertIsNotNone(verdict, "skip must still print one JSON verdict")
        # contract-shaped: required keys present and status agrees with exit code.
        for key in ("gate", "tier", "status", "summary", "findings", "confidence"):
            self.assertIn(key, verdict, "verdict missing contract key %r" % key)
        self.assertEqual(verdict.get("status"), "skip",
                         "status must agree with exit code 3 (skip)")

    def test_quoted_key_json_secret_escalates_med(self):
        # @req:REQ-006 quoted-key JSON "api_key": "<24+ chars>" -> exit 2 + med.
        literal = "z" * 30  # 30 chars, over the 24 min_token_length
        target = write(
            os.path.join(self.tmp, "creds.json"),
            "{\n"
            "  \"name\": \"service\",\n"
            "  \"api_key\": \"%s\"\n"
            "}\n" % literal,
        )
        policy = write_policy(self.tmp, "secret-scan", {"min_token_length": 24})
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 2,
                         "quoted-key JSON secret should escalate; stdout=%r" % raw)
        self.assertTrue(self._med(verdict), "expected a med-severity finding")
        matched = [f for f in findings_for_file(verdict, "creds.json")
                   if f.get("severity") == "med"]
        self.assertTrue(matched, "med finding must name creds.json")
        self.assertEqual(matched[0]["location"].rsplit(":", 1)[1], "3",
                         "the api_key JSON entry is on line 3")

    def test_unquoted_env_style_secret_escalates_med(self):
        # @req:REQ-006 unquoted env-style API_KEY=<24+ chars> -> exit 2 + med.
        literal = "w" * 30  # 30 chars, over the 24 min_token_length
        target = write(
            os.path.join(self.tmp, "service.env"),
            "NAME=service\n"
            "API_KEY=%s\n" % literal,
        )
        policy = write_policy(self.tmp, "secret-scan", {"min_token_length": 24})
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        self.assertEqual(code, 2,
                         "unquoted env-style secret should escalate; stdout=%r" % raw)
        self.assertTrue(self._med(verdict), "expected a med-severity finding")
        matched = [f for f in findings_for_file(verdict, "service.env")
                   if f.get("severity") == "med"]
        self.assertTrue(matched, "med finding must name service.env")
        self.assertEqual(matched[0]["location"].rsplit(":", 1)[1], "2",
                         "the API_KEY env line is line 2")

    def test_malformed_allowlist_regex_does_not_crash(self):
        # @req:REQ-007 un-compilable allowlist regex must not crash the gate;
        # the AWS key is still detected (exit 1) and never an internal error.
        target = write(
            os.path.join(self.tmp, "config.py"),
            "AWS_KEY = '%s'\n" % fake_aws_key(),
        )
        policy = write_policy(
            self.tmp, "secret-scan",
            {"allowlist": ["[invalid("]},
        )
        code, verdict, raw = run_gate(SECRET_SCAN, target, policy, self.tmp)

        # Crucial: a bad regex must not be reported as an internal error.
        self.assertLess(code, 10,
                        "malformed allowlist must not be an internal error; "
                        "stdout=%r" % raw)
        self.assertEqual(code, 1,
                         "the AWS key is still detected despite the bad regex; "
                         "stdout=%r" % raw)
        self.assertTrue(self._high(verdict),
                        "expected the AWS key to still produce a high finding")


if __name__ == "__main__":
    unittest.main()
