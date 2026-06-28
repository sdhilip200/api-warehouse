# Auth Patterns Reference

This file maps each authentication style to the exact `auth` dict consumed by `pipeline.build_rest_api_config(spec, secrets)`.

## Spec Shape

The `auth` key lives at the top level of the endpoints spec passed to `build_rest_api_config`:

```python
spec = {
    "base_url": "https://api.example.com",
    "auth": { ... },   # <-- one of the patterns below
    "paginator": { ... },
    "resources": [ ... ],
}
```

---

## 1. No Authentication

Use when the API is public and requires no credentials.

```json
{
  "type": "none"
}
```

`build_rest_api_config` will omit the `auth` key from the dlt client config entirely.

---

## 2. Bearer Token

Use for APIs that accept `Authorization: Bearer <token>` headers.

```json
{
  "type": "bearer",
  "token_env": "MY_API_TOKEN"
}
```

- `token_env` is the **name** of the environment variable (or `.dlt/secrets.toml` key) that holds the token value.
- At runtime, `secrets["MY_API_TOKEN"]` is resolved and placed into the dlt auth config.
- Never put the literal token in the spec.

---

## 3. API Key — Header

Use for APIs that accept a custom header such as `X-API-Key: <key>`.

```json
{
  "type": "api_key",
  "name": "X-API-Key",
  "location": "header",
  "token_env": "MY_API_KEY"
}
```

- `name`: the header name (case-sensitive).
- `location`: `"header"` (default when omitted).
- `token_env`: env-var name holding the key value.

---

## 4. API Key — Query Parameter

Use for APIs that accept a key as a query param such as `?api_key=<key>`.

```json
{
  "type": "api_key",
  "name": "api_key",
  "location": "query",
  "token_env": "MY_API_KEY"
}
```

- `name`: the query parameter name.
- `location`: `"query"`.

---

## 5. HTTP Basic Auth (v1 workaround)

dlt supports `HttpBasicAuth` directly. For v1 of this plugin, encode credentials as a Bearer token (base64 of `user:password`) or supply the pre-encoded value via:

```json
{
  "type": "bearer",
  "token_env": "MY_BASIC_AUTH_B64"
}
```

Set the env var to the base64-encoded `user:password` string. A native `basic` type may be added in a future version.

---

## 6. OAuth2 Client Credentials (v1 out-of-band)

OAuth2 token endpoints require a separate exchange step. For v1, obtain the access token out-of-band (e.g. via a pre-step script or Airflow sensor), store it in an env var, then treat it as a bearer token:

```json
{
  "type": "bearer",
  "token_env": "OAUTH2_ACCESS_TOKEN"
}
```

Automated token refresh will be addressed in a future version.

---

## Security

Always store the actual secret value in env vars or `.dlt/secrets.toml`. See `references/security.md` for the full policy.
