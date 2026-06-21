"""Shared helpers for the security-gate tests.

These tests invoke the gate scripts as black boxes over the standard gate
contract. They never import gate implementation code.
"""

import json
import pathlib
import subprocess
import sys


# <sdlc> is three levels up from this test directory:
#   <sdlc>/examples/security-gates/test/_util.py  -> parents[3] == <sdlc>
SDLC_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = SDLC_ROOT / "scripts"

SECRET_SCAN = SCRIPTS / "secret-scan"
DIFF_BUDGET = SCRIPTS / "diff-budget"


def run_gate(script_path, changed, policy_path, context):
    """Run a gate script with the standard contract flags.

    `changed` may be a single path/string or a list of them.
    Returns (returncode, parsed_verdict_dict, raw_stdout).
    """
    if isinstance(changed, (str, pathlib.Path)):
        changed = [changed]
    changed = [str(c) for c in changed]

    cmd = [sys.executable, str(script_path),
           "--changed", *changed,
           "--policy", str(policy_path),
           "--context", str(context)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    verdict = parse_last_json(proc.stdout)
    return proc.returncode, verdict, proc.stdout


def parse_last_json(stdout):
    """Parse the verdict the way the runner does: the last line of stdout that
    is a single JSON object. Returns None if no such line exists."""
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (ValueError, json.JSONDecodeError):
            continue
        if isinstance(obj, dict):
            return obj
    return None


def write(path, text):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def write_policy(tmpdir, gate_name, options):
    """Write a minimal policy.json with options under gates.<gate_name>."""
    policy = {"gates": {gate_name: options}}
    path = pathlib.Path(tmpdir) / "policy.json"
    path.write_text(json.dumps(policy))
    return path


def findings_for_file(verdict, filename):
    """All findings whose location names the given file (location is
    `file:line` or `file`)."""
    out = []
    for f in verdict.get("findings", []):
        loc = f.get("location", "")
        loc_file = loc.split(":", 1)[0]
        if loc_file.endswith(filename) or filename in loc:
            out.append(f)
    return out
