# Contributing to FoFo

Thanks for helping make AI-written tests trustworthy.

## Ground rules (they mirror the skill's own philosophy)

1. **Enforcement is a script, not prose.** If a rule must hold, it belongs in a gate
   with a real exit code — not in `SKILL.md` text. PRs that add an enforceable rule
   as prose will be asked to move it into a gate.
2. **Stack-agnostic by contract.** New gates obey the one I/O contract in
   [`gate-contract.md`](./plugins/fofo/skills/sdlc/references/gate-contract.md):
   `--changed --policy [--context] [--config]`, one JSON verdict on stdout, exit
   `0/1/2/3` (`>=10` = internal error).
3. **Dependency-light.** Kept gates use Python 3 stdlib only; `intent-gate` uses a
   vendored parser (no `npm install`). Don't add a runtime dependency a user must
   install. Bring-your-own tools are wired via config, never hardcoded.
4. **No network at gate runtime** except the user-configured model endpoint.

## Project layout

```
plugins/fofo/skills/sdlc/      # the skill + gate scripts (the real work)
plugins/fofo/agents/           # Judge + Reviewer subagent definitions
assets/                        # branding (generated; see BRANDING.md)
.claude-plugin/marketplace.json
```

## Develop & test

```bash
# run the full smoke test (proves the 7 acceptance criteria end to end)
cd plugins/fofo/skills/sdlc/examples/sample-feature && bash smoke.sh

# try the plugin live without publishing
claude --plugin-dir ./plugins/fofo

# validate the manifests
claude plugin validate ./plugins/fofo
claude plugin validate .
```

Enable the pre-push gate so you (or an agent) can't push the repo red — it runs
`selftest` + both smoke suites and refuses the push on any failure (this is what
would have caught the frm-1021 regression):

```bash
git config core.hooksPath .githooks
```

The same suites run in CI (`.github/workflows/ci.yml`) on every push and PR.

Any change to a gate must keep `smoke.sh` green. If you add a gate, add a check for
it in `smoke.sh` and a row in the README gate table.

## Adding a gate

1. Write the script under `plugins/fofo/skills/sdlc/scripts/` (Python 3 stdlib, or
   document the runtime). Top-of-file comment: what it checks, its contract, its
   config keys.
2. Add its options to `policy.schema.json` and a default to `policy.json`.
3. Add an entry to `gates.config.example` (disabled by default if heavy/BYO).
4. Map its failure `route` (`code` / `tests` / `spec`) in `gate-runner`.
5. Add a smoke-test check and a README row.

## Commits & PRs

- Keep PRs reviewable (the skill ships a `diff-budget` idea for a reason).
- Describe what changed and how you verified it. Paste smoke output for gate changes.
- Bump `version` in both `plugin.json` and `marketplace.json` for releases; tag with
  `claude plugin tag ./plugins/fofo`.

## Code of conduct

Be kind, be specific, assume good faith. Security issues: please open a private
report rather than a public issue.
