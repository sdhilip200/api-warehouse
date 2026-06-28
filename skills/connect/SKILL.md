---
name: connect
description: >
  Use this skill when the user wants to connect to an API, set up API
  authentication, configure API credentials, or test that API credentials are
  working. Trigger phrases include: "connect to the API", "set up auth",
  "configure my API key", "test my credentials", "verify my token", or any
  request to prove reachability before building a pipeline.
---

# connect — Secure Auth Setup and Smoke Test

## Overview

This skill establishes a working, env-var-based credential for an API and
confirms the connection with a single minimal authenticated request. Later
skills (assess, land, validate) assume this step is complete.

---

## Step 1 — Read the Security Policy

Before touching any credentials, read `references/security.md` and follow
every rule in it. The key constraints are:

- **Never paste a real secret into the chat or into source code.**
- **Never print, log, or store secret values.**
- Reference secrets by env-var name only (e.g. `"token_env": "MY_API_TOKEN"`).
- Scrub any example API responses before sharing them.

---

## Step 2 — Determine the Auth Type

Check the API's documentation (or inspect an existing endpoint spec if one
exists) to identify which auth pattern applies. The canonical list of patterns
is in `references/auth-patterns.md`. Common types:

| Pattern | When to use |
|---|---|
| `none` | Public API, no credentials required |
| `bearer` | `Authorization: Bearer <token>` header |
| `api_key` (header) | Custom header such as `X-API-Key` |
| `api_key` (query) | Token appended as a query parameter |
| `bearer` (base64) | HTTP Basic Auth encoded as Bearer token |

Record the auth type and the exact header/parameter name the API expects.

---

## Step 3 — Store the Credential Securely

**Do not ask the user to paste their secret into the chat.** Instead, direct
them to one of the two approved storage methods:

### Option A — Environment variable (recommended for CI/CD)

```bash
export MY_API_TOKEN="<your-token-value>"
```

Replace `MY_API_TOKEN` with the env-var name that matches the `token_env`
field you will use in the spec (e.g. `GITHUB_TOKEN`, `STRIPE_API_KEY`, etc.).
Run any pipeline commands in the same shell session.

### Option B — `.dlt/secrets.toml` (recommended for local development)

Create or edit `.dlt/secrets.toml` in the project root (already in
`.gitignore`):

```toml
[sources.my_source]
MY_API_TOKEN = "<your-token-value>"
```

Replace `my_source` with the dlt source name and `MY_API_TOKEN` with the
correct env-var name. **Never commit this file.**

See `references/security.md` for the full policy on scoping keys in
`secrets.toml` and how to extract them before passing to
`build_rest_api_config`.

---

## Step 4 — Run the Smoke Test

With the credential set, make a single minimal authenticated request to
confirm reachability and auth validity. Use `curl` (or Python `requests`) so
no pipeline code is needed at this stage.

```bash
# Bearer token example
curl -s -D - -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $MY_API_TOKEN" \
  "https://api.example.com/v1/me"
```

```bash
# API-key header example
curl -s -D - -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: $MY_API_KEY" \
  "https://api.example.com/v1/ping"
```

Replace the URL with the lightest endpoint the API offers (e.g. `/me`,
`/ping`, `/status`, or the first item in a small collection). Capture both
the HTTP status code and the response headers.

---

## Step 5 — Report the Result

Report the outcome in plain language:

| Outcome | What to say |
|---|---|
| HTTP 200 (or 2xx) | "Reachable — auth valid. Rate-limit headers: `X-RateLimit-Remaining: N`." |
| HTTP 401 | "Auth failed (401). Check that `MY_API_TOKEN` is exported in the current shell and matches the token from the API dashboard." |
| HTTP 403 | "Authenticated but forbidden (403). The token may lack the required scope/permission. Check API dashboard permissions." |
| HTTP 429 | "Rate-limited (429). Wait and retry, or use a different endpoint for the smoke test." |
| Connection error | "Cannot reach `api.example.com`. Check the base URL in the docs, your network/VPN, and whether the API is in a private region." |

Always include:
- **Reachable?** (yes / no / error)
- **Auth valid?** (yes / no / unclear)
- **Rate-limit headers** (print names and values seen; replace any token
  values with `<REDACTED>` before sharing)

On failure, give one specific next step — not a list of everything that could
be wrong.
