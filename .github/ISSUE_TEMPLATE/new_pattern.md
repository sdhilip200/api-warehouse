---
name: New pattern proposal
about: Propose a new auth, pagination, or destination pattern
title: "[pattern] "
labels: pattern
assignees: ''
---

## Pattern type

- [ ] Auth pattern (`references/auth-patterns.md`)
- [ ] Pagination pattern (`references/pagination-patterns.md`)
- [ ] Destination (`references/destinations.md`)

## Pattern name

<!-- e.g. "OAuth 2.0 Client Credentials", "cursor pagination", "Snowflake" -->

## What API or destination prompted this?

<!-- Link to the API docs or destination docs -->

## Detection heuristics

<!-- How should the assess skill detect this pattern from human-readable docs? What strings, fields, or response shapes signal it? -->

## dlt config snippet

```python
# Minimal dlt rest_api / destination config for this pattern
```

## Security notes

<!-- Any credentials required? How should they be stored? (env var name convention) -->

## Have you tested this against a real API?

- [ ] Yes — API name: ___
- [ ] No (proposal only)
