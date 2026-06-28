# MEMORY — api-warehouse run quirks

Append one line per notable end-to-end run. The orchestrator reads this at
start to avoid repeating known pitfalls and appends after each completed run.

Format: `YYYY-MM-DD | <api-name> | <quirk>`

---

<!-- Example entry (remove when real entries exist): -->
<!-- 2026-06-01 | stripe-invoices | Pagination cursor resets on 429; added 2 s backoff in connect step before assess would succeed. -->
