# fofo

Test-first agentic development loop with separated authorship and judgment, packaged
as a Claude Code plugin.

- **Skill:** `/fofo:sdlc` — the procedure and phase/role choreography.
- **Subagents:** `fofo-judge` (writes tests from the spec, spec-only) and
  `fofo-reviewer` (fresh-eyes Tier-1 review). Both auto-load into `/agents`.
- **Gate scripts:** `skills/sdlc/scripts/` — `gate-runner` plus `spec-lint`,
  `trace-gate`, `redgreen-gate`, `intent-gate` (real-AST JS/TS analysis via a
  vendored parser), `separation-gate`, and the model-based `semantic-test-judge` /
  `fresh-eyes-review`.

Full docs live in `skills/sdlc/`: `SKILL.md`, `INSTALL.md`, `references/`, and a
runnable `examples/sample-feature/smoke.sh`.

## Per-repo setup

After installing the plugin, in each repo you use it on (the installed skill lives
under `~/.claude/plugins/marketplaces/fofo-marketplace/plugins/fofo/skills/sdlc/`):

```bash
SDLC="$HOME/.claude/plugins/marketplaces/fofo-marketplace/plugins/fofo/skills/sdlc"
cp "$SDLC/gates.config.example" gates.config
cp "$SDLC/policy.json" policy.json
```

Then set your test command in `policy.json` → `gates.redgreen-gate.test_command`.
Heavy/BYO and model gates are disabled by default; enable them in `gates.config`.
Or just run `/fofo:sdlc` and let the skill choreograph the phases.
