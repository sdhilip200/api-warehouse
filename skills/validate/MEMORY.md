# validate — API Quirk Memory

Seed file for reconciliation quirks discovered during prior runs. Add one entry per API
when you find a behaviour that affects how checks are interpreted or skipped. Keep entries
to one line each; delete stale entries when the API changes.

Format: `<API name> — <quirk> — <consequence for validate>`

---

## Entries

- **JSONPlaceholder** — exposes no total-count header or `X-Total-Count`; pagination ends
  when the response array is empty — validate by checking load success + sampling; the
  `row_count` check will be `skipped` unless the full table is queried directly.
