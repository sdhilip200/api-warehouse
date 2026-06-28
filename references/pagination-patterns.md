# Pagination Patterns Reference

This file maps common API pagination cues to the exact `paginator` dict consumed by `pipeline.build_rest_api_config(spec, secrets)`.

## Spec Shape

The `paginator` key lives at the top level of the endpoints spec:

```python
spec = {
    "base_url": "https://api.example.com",
    "auth": { ... },
    "paginator": { ... },   # <-- one of the patterns below
    "resources": [ ... ],
}
```

If `paginator` is absent or `{"type": "single_page"}`, dlt makes a single request and stops.
Note: for single-page APIs, dlt may log "Fallback paginator used: SinglePagePaginator" — this is expected and harmless; the builder intentionally omits the paginator key for `single_page`.

---

## 1. Single Page (no pagination)

Use when the API returns all results in one response.

**Detection cues:** No `next`, `cursor`, `page`, or `offset` fields in the response. Total result count is small or unknown.

```json
{
  "type": "single_page"
}
```

---

## 2. Page Number (`?page=N`)

Use when the API accepts a `page` (or `pageNumber`) query parameter.

**Detection cues:** Response contains `page`, `total_pages`, or `has_more`. URL pattern includes `?page=`.

```json
{
  "type": "page_number",
  "page_param": "page",
  "total_pages_path": "meta.total_pages"
}
```

- `page_param`: query parameter name (commonly `page` or `pageNumber`).
- `total_pages_path`: dot-separated JSON path to the total page count in the response. Omit if the API uses a `has_more` boolean instead.

---

## 3. Offset / Limit (`?offset=N&limit=M`)

Use when the API accepts `offset` and `limit` (or `skip`/`count`) query parameters.

**Detection cues:** URL or docs mention `offset`, `skip`, `limit`, `count`. Response may include `total` count.

```json
{
  "type": "offset",
  "limit": 100,
  "offset_param": "offset",
  "limit_param": "limit",
  "total_path": "total"
}
```

- `limit`: page size to request each call.
- `offset_param` / `limit_param`: query param names.
- `total_path`: dot-path to total record count in the response (used to stop iteration).

---

## 4. JSON Link (next URL in response body)

Use when the API embeds the full URL of the next page in the response body.

**Detection cues:** Response contains a `next`, `next_url`, or `links.next` field that is a full URL string.

```json
{
  "type": "json_link",
  "next_url_path": "links.next"
}
```

- `next_url_path`: dot-path to the next-page URL in the response JSON.
- Iteration stops when the field is `null` or absent.

---

## Out-of-Spec (dlt-Native) Paginator Types

The four types above (`single_page`, `page_number`, `offset`, `json_link`) are the **formally-documented spec types** — the only ones the plugin contract explicitly enumerates and tests.

The two types below (`cursor` and `header_link`) are **dlt-native paginators passed through unmodified** by `pipeline.py` (the plugin simply forwards any `paginator` dict to dlt without inspecting the `type` field). They work at runtime if dlt supports them, but they are **NOT part of the four-type formal spec contract**. Use them only if you have confirmed the exact dlt paginator key names against the installed dlt version.

### cursor (dlt-native, out-of-spec)

> **Not a formal spec type.** Passed through to dlt unmodified. Verify key names against your dlt version before using.

Use when the API returns an opaque cursor or `next_token` in the response body.

**Detection cues:** Response contains a `cursor`, `next_cursor`, `next_token`, or `continuation_token` field. The next request sends this value back as a query param.

```json
{
  "type": "cursor",
  "cursor_path": "meta.next_cursor",
  "cursor_param": "cursor"
}
```

- `cursor_path`: dot-path to the cursor value in the response JSON.
- `cursor_param`: query parameter name to send the cursor back.

### header_link (dlt-native, out-of-spec)

> **Not a formal spec type.** Passed through to dlt unmodified. Verify key names against your dlt version before using.

Use when the API follows RFC 5988 and puts the next URL in an HTTP `Link` response header.

**Detection cues:** API docs mention `Link` header; tools like `curl -I` show `Link: <...>; rel="next"`.

dlt handles this natively via `HeaderLinkPaginator`. In the spec, express it as:

```json
{
  "type": "header_link"
}
```

No additional fields are required.

---

## Selection Guide

| Signal in API response / docs | Use paginator type | Formal spec type? |
|---|---|---|
| No next-page signal | `single_page` | Yes |
| `?page=` query param | `page_number` | Yes |
| `?offset=` + `?limit=` | `offset` | Yes |
| Full URL in response body (`next`) | `json_link` | Yes |
| Opaque cursor token in body | `cursor` *(dlt-native, out-of-spec)* | No |
| `Link` HTTP header | `header_link` *(dlt-native, out-of-spec)* | No |
