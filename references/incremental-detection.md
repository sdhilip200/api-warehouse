# Incremental Detection Reference

This file is the senior-DE checklist for deciding whether an API endpoint supports incremental loading, and how to express that in the endpoints spec consumed by `pipeline.build_rest_api_config`.

## What "Incremental" Means Here

An endpoint is **incrementally loadable** when:
1. The API accepts a filter parameter that limits results to records modified after a given timestamp or cursor, AND
2. The response includes a field that advances the cursor/timestamp for the next run.

Without both, a full reload (`replace` write disposition) is the only safe option.

---

## Detection Checklist

Work through these checks in order. Stop as soon as you have evidence for or against incremental support.

### Step 1 — Scan Query Parameters

Look for any of these patterns in the API docs or an example request URL:

| Parameter name | Meaning |
|---|---|
| `updated_since` | Records updated after this timestamp |
| `modified_after` | Records modified after this timestamp |
| `since` | General "since" timestamp filter |
| `start_date` | Records from this date forward |
| `from_date` | Records from this date forward |
| `after_cursor` | Records after this opaque cursor |
| `min_updated_at` | Lower bound on last-modified field |

If any of these (or close variants) exist, **incremental is likely supported**.

### Step 2 — Scan Response Fields

Look for sortable timestamp or cursor fields in the response JSON:

| Field name | Use |
|---|---|
| `updated_at` | Standard ISO-8601 last-modified timestamp |
| `modified_at` | Variant of `updated_at` |
| `last_modified` | HTTP-style last-modified date |
| `timestamp` | Generic timestamp (verify it tracks mutation, not creation) |
| `cursor` / `next_cursor` | Opaque cursor that advances with new data |

The field you find here becomes `incremental.cursor_path` in the spec.

### Step 3 — Check for Change Feeds or Webhooks

Some APIs expose a `/changes`, `/events`, or `/audit` endpoint that streams only modified records. If present, document it separately — it may require a different pipeline pattern.

---

## Verdict Format

Emit one of these two JSON objects as the output of an incremental assessment:

**Supported:**
```json
{
  "supported": true,
  "evidence": "Query param 'updated_since' accepts ISO-8601; response field 'updated_at' advances the cursor."
}
```

**Not supported:**
```json
{
  "supported": false,
  "reason": "No date/cursor filter param found in docs; response has no sortable timestamp field."
}
```

**Rule: never claim `supported: true` without a named filter parameter OR a named cursor/updated-at response field as evidence.** A cursor-in-response change feed with no filter param can still be incrementally loadable; requiring both would cause valid incremental endpoints to be mis-classified as unsupported. Guessing (claiming `supported: true` with no evidence at all) leads to silent data gaps.

---

## Spec Shape for Incremental Endpoints

When incremental is supported, populate the `incremental` key inside the resource:

```python
spec = {
    "base_url": "https://api.example.com",
    "auth": { "type": "bearer", "token_env": "API_TOKEN" },
    "resources": [
        {
            "name": "orders",
            "path": "/orders",
            "primary_key": "id",
            "incremental": {
                "cursor_path": "updated_at",       # dot-path to the advancing field in each record
                "param": "updated_since",           # query param name to send to the API
                "initial_value": "2020-01-01T00:00:00Z"  # first-run starting point
            }
        }
    ]
}
```

`build_rest_api_config` translates this into:
- `endpoint["incremental"]["cursor_path"]` and `endpoint["incremental"]["initial_value"]`
- `endpoint["params"][param] = "{incremental.start_value}"`
- `write_disposition = "merge"` (requires `primary_key`)

When `incremental` is `null` or absent, `write_disposition` is set to `"replace"` (full reload each run).

---

## Common Pitfalls

- **Creation timestamp only** (`created_at`): does not advance on updates — not suitable as a cursor.
- **Server-side sorting not guaranteed**: if records can be returned out of order even with a `since` filter, you may miss records. Check API docs for ordering guarantees.
- **Token expiry during long runs**: for very large datasets, ensure auth tokens do not expire mid-run (see `references/auth-patterns.md`).
