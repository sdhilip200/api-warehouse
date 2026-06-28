# MEMORY — API-specific quirks seen during assess runs

One line per entry: `API name | quirk type | detail`. Append new entries in Step 6d; do not edit existing ones.

---

## Example entry format

```
Stripe API | cursor pagination | uses `starting_after` (object id, not timestamp); response field is `has_more` not `next_cursor`
```

---

## Entries

<!-- append new entries below this line -->
