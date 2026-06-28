# Contributing to api-warehouse

Thank you for considering a contribution. The plugin is designed to be extended primarily through **reference docs** — you rarely need to touch skill logic.

---

## How to add a new pattern

### New auth pattern
Add an entry to [`references/auth-patterns.md`](references/auth-patterns.md) following the existing format:
- Name and description
- How to detect it from API docs
- The environment variable convention (e.g. `API_KEY`)
- A minimal dlt `rest_api` config snippet

### New pagination pattern
Add an entry to [`references/pagination-patterns.md`](references/pagination-patterns.md):
- Pattern name (e.g. `cursor`, `offset`, `link-header`)
- Detection heuristics (what strings/fields signal this pattern)
- The dlt paginator config snippet

### New destination
Add an entry to [`references/destinations.md`](references/destinations.md):
- Destination name
- Required secrets and how to set them
- The dlt credentials block
- Any destination-specific caveats (e.g. schema naming rules)

---

## How to add a new skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter (`name:`, `description:`, `tools:`).
2. Implement the skill body following the patterns in existing skills (`assess`, `land`, `validate`).
3. Register it in `.claude-plugin/plugin.json` under `"skills"`.
4. Add a structural test asserting the load-bearing strings are present (see `tests/test_plugin_structure.py`).

---

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

For verbose output:

```bash
pytest -v
```

The test suite covers plugin structure, library unit tests, and an end-to-end integration test against JSONPlaceholder (no API key required).

---

## Security and honesty rules (required for all PRs)

These are not optional guidelines — they are **hard requirements**:

1. **Secrets never hardcoded.** No API keys, tokens, or passwords in any skill, test, example, or reference doc. Secrets must come from environment variables or `.dlt/secrets.toml`.
2. **Secrets never echoed.** Skills must not print, log, or include secret values in output.
3. **Honest confidence.** Skills must not claim capabilities they don't have. Validation reports must admit gaps (e.g., "source count unavailable — skipped"). Incremental verdicts must cite evidence from the API docs.
4. **Input guard.** The `assess` skill must reject input that is not API documentation with a clear message: "This doesn't look like API documentation."
5. **Scope guard.** No transformation, no auto-deploy into user cloud, no MCP destination connections.

---

## PR checklist

- [ ] Tests pass locally (`pytest -v`)
- [ ] No secrets hardcoded or echoed
- [ ] Reference doc entries follow the existing format (name, detection, config snippet)
- [ ] Structural test updated if a new load-bearing string was added
- [ ] `CONTRIBUTING.md` updated if you added a new contribution path
- [ ] PR description explains *what* and *why*, not just *what*
