"""
gatelib.py — shared helpers for FoFo Agentic SDLC gates.

What it provides:
  - The single I/O contract every gate obeys (parse args, emit JSON, map exit codes).
  - Small stack-agnostic utilities: glob expansion for --changed, file reading,
    policy/config loading.

The gate contract (see references/gate-contract.md):
  Invocation:  <gate> --changed <paths/globs> --policy <policy.json> [--context <dir>] [--config <gates.config>]
  stdout:      one JSON object {gate, tier, status, summary, findings[], confidence}
  exit codes:  0 pass · 1 fail · 2 escalate · 3 skip · >=10 internal error

This module has zero third-party dependencies (Python 3 stdlib only) so a gate
written against it runs on a fresh install with nothing else installed.
"""

import argparse
import glob
import json
import os
import sys

# status -> process exit code
STATUS_EXIT = {"pass": 0, "fail": 1, "escalate": 2, "skip": 3}
INTERNAL_ERROR_EXIT = 10


def parse_args(argv=None):
    """Parse the standard gate contract arguments.

    --changed may be repeated and/or comma/space separated. Returns an argparse
    Namespace with: changed (list[str] of raw patterns), policy, context, config,
    plus any extra known flags a specific gate adds via `extra`.
    """
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--changed", action="append", default=[],
                   help="Changed paths or globs (repeatable; comma/space separated).")
    p.add_argument("--policy", default=None, help="Path to policy.json.")
    p.add_argument("--context", default=".", help="Project/context root directory.")
    p.add_argument("--config", default=None, help="Path to gates.config (orchestration).")
    return p, p.parse_known_args(argv)[0]


def split_patterns(changed):
    """Flatten the --changed values into a clean list of patterns."""
    out = []
    for item in changed or []:
        for chunk in str(item).replace(",", " ").split():
            chunk = chunk.strip()
            if chunk:
                out.append(chunk)
    return out


def expand_changed(changed, root="."):
    """Expand --changed patterns into existing file paths, rooted at `root`.

    A bare path that exists is returned as-is. Globs are expanded recursively.
    Returns a sorted, de-duplicated list of files that exist.
    """
    files = set()
    for pat in split_patterns(changed):
        candidates = [pat]
        if not os.path.isabs(pat):
            candidates.append(os.path.join(root, pat))
        matched = False
        for cand in candidates:
            if any(ch in cand for ch in "*?[]"):
                for m in glob.glob(cand, recursive=True):
                    if os.path.isfile(m):
                        files.add(os.path.normpath(m))
                        matched = True
            elif os.path.isfile(cand):
                files.add(os.path.normpath(cand))
                matched = True
            elif os.path.isdir(cand):
                for dirpath, _dirs, names in os.walk(cand):
                    for n in names:
                        files.add(os.path.normpath(os.path.join(dirpath, n)))
                matched = True
            if matched:
                break
    return sorted(files)


def load_json(path, default=None):
    """Load a JSON file; return `default` if path is missing/None."""
    if not path or not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_policy(args):
    """Load policy.json (from --policy or the conventional ./policy.json)."""
    path = args.policy
    if not path:
        guess = os.path.join(args.context or ".", "policy.json")
        path = guess if os.path.isfile(guess) else None
    return load_json(path, default={}) or {}


def load_config(args):
    """Load gates.config (from --config or the conventional ./gates.config)."""
    path = args.config
    if not path:
        guess = os.path.join(args.context or ".", "gates.config")
        path = guess if os.path.isfile(guess) else None
    return load_json(path, default={}) or {}


def gate_options(policy, gate_name):
    """Per-gate options live under policy['gates'][gate_name]."""
    return (policy.get("gates", {}) or {}).get(gate_name, {}) or {}


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def finding(severity, location, detail):
    return {"severity": severity, "location": location, "detail": detail}


def emit(gate, tier, status, summary, findings=None, confidence=0.0):
    """Print the contract JSON to stdout and exit with the mapped code.

    Never returns — calls sys.exit. Use `fail_internal` for crashes.
    """
    obj = {
        "gate": gate,
        "tier": tier,
        "status": status,
        "summary": summary,
        "findings": findings or [],
        "confidence": round(float(confidence), 3),
    }
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()
    sys.exit(STATUS_EXIT.get(status, INTERNAL_ERROR_EXIT))


def fail_internal(gate, tier, message):
    """Emit an internal-error verdict and exit >=10 (hard stop for the runner)."""
    obj = {
        "gate": gate,
        "tier": tier,
        "status": "error",
        "summary": "gate internal error: " + str(message),
        "findings": [],
        "confidence": 0.0,
    }
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()
    sys.exit(INTERNAL_ERROR_EXIT)
