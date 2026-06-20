# Install

The unit of portability is the `fofo-agentic-sdlc/` folder. Copy it into the
host's skills directory; nothing else is required beyond a POSIX shell, Python 3
(for the kept gates) and Node (only for the JS/TS `intent-gate`).

## Claude Code (primary)

**Personal** (all your projects):
```bash
cp -R fofo-agentic-sdlc ~/.claude/skills/fofo-agentic-sdlc
```

**Project** (this repo only, check it into git):
```bash
mkdir -p .claude/skills
cp -R fofo-agentic-sdlc .claude/skills/fofo-agentic-sdlc
```

Start a new session (or, if the `.claude/skills/` directory already existed, the
change is picked up live). Confirm with `/skills` — you should see
`fofo-agentic-sdlc`. Claude loads it automatically on spec-to-code tasks, or invoke
it with `/fofo-agentic-sdlc`.

**Per-repo setup** (once): from your repo root,
```bash
cp ~/.claude/skills/fofo-agentic-sdlc/gates.config.example gates.config
cp ~/.claude/skills/fofo-agentic-sdlc/policy.json policy.json
```
then set `policy.gates.redgreen-gate.test_command` to your test command.

**Sub-agents (role separation).** Copy the ready definitions so the Judge and
Reviewer run as separate contexts:
```bash
mkdir -p .claude/agents
cp ~/.claude/skills/fofo-agentic-sdlc/agents/*.md .claude/agents/
```
Restart the session so they load. They appear in `/agents`. Without them, the
skill falls back to sequential fresh-context passes plus `separation-gate`.

**Zip for upload (claude.ai / API):** the folder must contain `SKILL.md` at its
root.
```bash
cd fofo-agentic-sdlc && zip -r ../fofo-agentic-sdlc.zip . && cd ..
```
Upload via claude.ai Settings → Features, or the Skills API. Note: on the Claude
API and claude.ai the runtime has **no/limited network**, so the Tier-1 model
gates won't reach an external endpoint there — use them in Claude Code or any host
with network access. The Tier-0 gates run anywhere Python 3 is available.

**Plugin / marketplace (recommended for sharing):** packaged as the `fofo` plugin,
other people install it with two commands and the Judge/Reviewer subagents auto-load
(no manual `.claude/agents/` copy):

```text
/plugin marketplace add Sweet-Papa-Technologies/Agentic-SDLC
/plugin install fofo@fofo-marketplace
```

The skill is then invoked as `/fofo:sdlc` (plugin skills are namespaced). The repo
[`Sweet-Papa-Technologies/Agentic-SDLC`](https://github.com/Sweet-Papa-Technologies/Agentic-SDLC)
is both the project home and the marketplace (`.claude-plugin/marketplace.json` at its
root). For quick local testing from a clone: `claude --plugin-dir ./plugins/fofo`.

## Other SKILL.md-consuming agents

The same folder works without code changes. Sub-agent orchestration uses native
features where present and falls back to sequential passes otherwise.

| Host | Skill directory | Sub-agents |
|------|-----------------|------------|
| **Cursor** | `.cursor/skills/fofo-agentic-sdlc/` | Fallback: sequential passes + `separation-gate` |
| **Codex CLI** | `.codex/skills/fofo-agentic-sdlc/` (per its skills config) | Fallback |
| **Gemini CLI** | `.gemini/skills/fofo-agentic-sdlc/` (per its skills/extensions config) | Fallback |

The gates are host-neutral: POSIX shebang entry points, the standard contract,
no Claude-Code-only assumptions. Any host that can run a shell command and read the
JSON verdict can drive them. Confirm the exact skills path against the host's
current docs — it is the one thing that varies.

## Requirements

- POSIX shell, Python 3.8+ (kept gates, `adapter`, `gate-runner`).
- Node 14+ only for the kept JS/TS `intent-gate`. Its AST parser (acorn) is
  **vendored in `scripts/vendor/`** — it ships with the skill, so there is nothing
  to `npm install` and no network at runtime; the gate falls back to a built-in
  token analyzer if the parser is absent or a file is TS/JSX. Skip or replace the
  gate for non-JS stacks — see references/porting-to-other-languages.md.
- For Tier-1 model gates: an API key in the env var named by
  `gates.config.model.api_key_env` (default `ANTHROPIC_API_KEY`).
- No global package installs. No external services. No network at gate runtime
  except the configured model endpoint.
