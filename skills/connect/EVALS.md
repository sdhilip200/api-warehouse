# EVALS — connect skill

Objective pass/fail checks for the connect step's output. Run these via the
loop in `../../references/running-evals.md` using a separate grader agent.

---

## Checks

### 1. Smoke test was executed
**Pass:** The output contains an actual HTTP status code returned by a live
request (e.g. `200`, `401`, `403`, `429`), not a placeholder or hypothetical.
**Fail:** The output describes what the command *would* do without showing a
real result.

### 2. Credential referenced by env-var name only
**Pass:** Every reference to the credential uses the env-var name
(e.g. `$MY_API_TOKEN`, `STRIPE_API_KEY`) and no secret value appears anywhere
in the output or in any logged command.
**Fail:** A token value, API key string, or password appears in plain text in
any part of the output.

### 3. No secret value in response snippets
**Pass:** Any API response shown to the user has been scrubbed — token fields
are replaced with `<REDACTED>` or omitted.
**Fail:** A bearer token, API key value, or credential string from the API
response appears in the shared output.

### 4. Reachability and auth verdict are explicit
**Pass:** The report clearly states both (a) whether the API was reachable and
(b) whether auth was valid — using those terms or unambiguous equivalents.
**Fail:** The report is ambiguous or omits one of the two verdicts.

### 5. Rate-limit headers captured (or skipped)
**Pass:** If the API returned any `X-RateLimit-*`, `RateLimit-*`, or
`Retry-After` headers, their names and values appear in the report (with any
embedded token values redacted).
**Skipped:** The API returned no rate-limit headers in the smoke-test response.
**Fail:** Rate-limit headers were present in the response but not reported.

### 6. Failure includes one specific next step
**Pass:** If the smoke test returned a non-2xx status, the report gives exactly
one concrete next action (e.g. "Re-export `MY_API_TOKEN` from the dashboard
and retry") rather than a generic troubleshooting list.
**Skipped:** The smoke test returned 2xx (no failure to diagnose).
**Fail:** The report lists multiple possible causes without identifying the
most likely one, or gives no next step at all.

### 7. Auth type recorded before running the test
**Pass:** The output or notes include the identified auth pattern (e.g.
`bearer`, `api_key` header, `api_key` query) and the exact header or parameter
name the API uses.
**Fail:** The smoke test was run without recording which auth pattern was
selected, making the step unrepeatable.
