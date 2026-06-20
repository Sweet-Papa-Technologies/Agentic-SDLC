"""
modellib.py — the ONLY network access in this skill.

Talks to the user-configured model endpoint for the AI-judge gates
(semantic-test-judge, fresh-eyes-review). Default request shape is the Anthropic
Messages API; a `base_url` override lets any Anthropic-compatible proxy stand in
without being a dependency. The API key is read from an env var whose NAME is
configured (never a literal key in any file).

No gate fetches arbitrary URLs — only the endpoint resolved here.
"""
import json
import os
import urllib.error
import urllib.request

DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"
ANTHROPIC_VERSION = "2023-06-01"


class NotConfigured(Exception):
    """Raised when the model endpoint/key isn't set — the gate should skip."""


def resolve(config):
    """Return a dict {url, model, api_key} or raise NotConfigured."""
    model_cfg = (config or {}).get("model", {}) or {}
    key_env = model_cfg.get("api_key_env", "ANTHROPIC_API_KEY")
    api_key = os.environ.get(key_env)
    if not api_key:
        raise NotConfigured("env var %s is not set (set api_key_env in gates.config)" % key_env)

    base_url = model_cfg.get("base_url")
    if base_url:
        url = base_url.rstrip("/") + "/v1/messages"
    else:
        url = model_cfg.get("endpoint", DEFAULT_ENDPOINT)
    return {
        "url": url,
        "model": model_cfg.get("model", DEFAULT_MODEL),
        "api_key": api_key,
        "version": model_cfg.get("anthropic_version", ANTHROPIC_VERSION),
        "max_tokens": int(model_cfg.get("max_tokens", 1024)),
        "timeout": int(model_cfg.get("timeout_seconds", 60)),
    }


def complete(resolved, system, user):
    """One non-streaming completion. Returns the model's text. Raises on transport error."""
    body = json.dumps({
        "model": resolved["model"],
        "max_tokens": resolved["max_tokens"],
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(resolved["url"], data=body, method="POST")
    req.add_header("content-type", "application/json")
    req.add_header("x-api-key", resolved["api_key"])
    req.add_header("anthropic-version", resolved["version"])
    with urllib.request.urlopen(req, timeout=resolved["timeout"]) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    # Anthropic shape: {"content": [{"type":"text","text":"..."}]}
    parts = payload.get("content", [])
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return text or json.dumps(payload)


def extract_json(text):
    """Pull the first balanced {...} object out of a model reply."""
    start = text.find("{")
    if start == -1:
        raise ValueError("model reply contained no JSON object")
    depth, instr, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
            continue
        if ch == '"':
            instr = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON in model reply")
