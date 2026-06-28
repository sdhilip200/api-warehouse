# Security Reference

## Golden Rules

1. **Never hardcode secrets.** API tokens, passwords, and keys must never appear in source code, generated pipeline files, reports, or log output.
2. **Never print or log secret values.** Even during debugging, do not emit secret values to stdout, stderr, or any log file.
3. **Reference secrets by env-var name only.** Generated pipelines store the env-var name (e.g. `"token_env": "MY_API_TOKEN"`) — the runtime resolves the value at execution time.
4. **Scrub example data.** When showing sample API responses, replace real tokens with `<REDACTED>` or a clearly fake placeholder like `sk-XXXX`.

## How to Supply Secrets at Runtime

### Option A — Environment variables (recommended for CI/CD)

```bash
export MY_API_TOKEN="your-actual-token-here"
export DB_PASSWORD="your-db-password-here"
```

Run the pipeline in the same shell session (or inject via your CI secrets manager).

### Option B — `.dlt/secrets.toml` (recommended for local dev)

Create `.dlt/secrets.toml` in your project root (it is already in `.gitignore`):

```toml
[sources.my_source]
MY_API_TOKEN = "your-actual-token-here"

[destination.postgres]
DB_PASSWORD = "your-db-password-here"
```

dlt reads this file automatically; you never need to load it manually.

**Never commit `.dlt/secrets.toml` to version control.**

## What the Plugin Does

When `build_rest_api_config(spec, secrets)` is called:
- `spec["auth"]["token_env"]` holds the env-var *name* (e.g. `"MY_API_TOKEN"`).
- `secrets` is a plain dict populated at runtime from env or `secrets.toml`.
- The resolved token value is placed into the dlt config object only — it is not stored, logged, or returned to the caller in a way that persists to disk.

## Checklist Before Sharing Generated Code

- [ ] No literal token, key, or password in the file.
- [ ] Every secret reference is an env-var name string such as `"token_env": "MY_API_TOKEN"`.
- [ ] Example responses have been scrubbed of real credentials.
- [ ] `.dlt/secrets.toml` is listed in `.gitignore`.
