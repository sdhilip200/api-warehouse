# EVALS — assess skill

Run these checks via the loop in `../../references/running-evals.md`. A separate grader agent reads only this file and the artifacts; it has no context from the skill run that produced them.

---

## Checks

| # | Name | What to check | Pass condition |
|---|------|---------------|----------------|
| 1 | input-guard-wording | When input lacks endpoints/methods/auth, the skill's reply | Contains the exact phrase "not API documentation" |
| 2 | endpoints-json-shape | `endpoints.json` top-level keys | Has `base_url` (string), `auth` (object with `type`), and `resources` (non-empty array) |
| 3 | endpoints-json-resources | Each entry in `resources[]` | Has `name`, `path`, `primary_key`; `incremental` is either `null` or an object with `cursor_path`, `param`, `initial_value` |
| 4 | incremental-verdict-evidence | The incremental block inside `endpoints.json` and in `assessment.html` | `supported: true` has a non-empty `evidence` string naming a field or param; `supported: false` has a non-empty `reason` string — never a bare boolean with no explanation |
| 5 | assessment-html-exists | `assessment.html` on disk | File exists and is non-empty HTML |
| 6 | assessment-html-verdict | Content of `assessment.html` | Contains the word "YES" or "NO" (the incremental verdict rendered by `render_assessment`) and a non-empty evidence/reason string beside it |
| 7 | samples-present | `samples/` directory | At least one `.json` file exists for the primary resource endpoint |
| 8 | no-bare-guess | Incremental verdict across all artifacts | No instance of "likely", "probably", "may support", or "unclear" without an accompanying `supported: false` and a reason |
| 9 | build-rest-api-compat | `endpoints.json` schema validity | Passes static schema validation: `auth.type` is one of `none`/`bearer`/`api_key`; `api_key` entries have `name` and `location`; `bearer`/`api_key` entries have `token_env`; `resources[]` entries have `name`, `path`, `primary_key`. |

`skipped` is valid only when the check cannot be computed from the artifacts (e.g., check 1 cannot be run if the grader was never shown the input-guard exchange).
