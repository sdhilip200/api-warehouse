# land — Evals

Run these checks on the generated `pipeline_land.py` using the loop defined in
`../../references/running-evals.md`. Spin up a grader agent with a clean context;
give it this file and the artifact only.

## Checks

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | `dataset_name="raw"` is set | `pipeline_land.py` contains `dataset_name="raw"` |
| 2 | No transformation logic | File contains no pandas/SQL transforms, no `.filter()`, `.map()`, `.transform()`, or inline data mutation before `pipeline.run()` |
| 3 | Secrets via env, never hardcoded | Any token/credential is read via `os.environ[...]` or a dlt secrets reference; no literal credential string appears in the file |
| 4 | Secrets not printed | No `print(token)` or `print(secrets)` call that would expose a credential in stdout |
| 5 | Correct dlt import | File contains `from dlt.sources.rest_api import rest_api_source` |
| 6 | `build_rest_api_config` called | File contains a call to `build_rest_api_config(spec` |
| 7 | Pipeline runs source | `pipeline.run(source)` appears in the file |
| 8 | Row counts reported | After `pipeline.run(source)`, the script prints `load_info` or iterates resources to report rows loaded per resource |

`skipped` where a check cannot be evaluated because the artifact is absent or the API
genuinely does not expose the required information.
