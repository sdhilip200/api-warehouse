# validate — Eval Checklist

Run this checklist per the loop in `../../references/running-evals.md`. Spin up a grader
agent with a clean context; give it this file and `validation.html` (plus the run log if
available). Return `pass` / `fail` / `skipped` with one line of evidence per check.

---

## Checks

1. **Both sides profiled.**
   The run log shows `profile_records` called on `source_records` and on `loaded_records`
   separately, producing two profile dicts. `skipped` if the log is unavailable.

2. **`reconcile` received both profiles.**
   The run log shows `reconcile(source_profile, loaded_profile)` called with the dicts
   from check 1, and its return value was passed directly to `render_validation`.
   `skipped` if the log is unavailable.

3. **`validation.html` exists and is non-empty.**
   The file exists on disk and contains at least one `<tr>` row in the checks table.

4. **Pass/fail/skipped counts are shown.**
   `validation.html` contains a summary line matching the pattern
   `N passed, N failed, N skipped` where the three numbers sum to the total row count
   in the checks table.

5. **No skipped check is labelled pass or fail.**
   Every row in `validation.html` where the status cell reads `skipped` has detail text
   that explains why the check could not be computed (e.g., "stat unavailable",
   "type differs", "column missing on one side"). No skipped check is listed as `pass`.

6. **Numeric control totals compared where possible.**
   If the source data contains numeric columns, `validation.html` includes at least one
   check with kind `numeric` (covering `sum`, `min`, or `max`). `skipped` if no numeric
   columns exist in the dataset.

7. **Timestamp range compared where possible.**
   If the source data contains timestamp columns, `validation.html` includes at least one
   check with kind `timestamp` (covering `min` or `max`). `skipped` if no timestamp
   columns exist.

8. **Row-count check present.**
   `validation.html` includes a check named `row_count` with status `pass`, `fail`, or
   `skipped`. A `skipped` row-count check must have detail text explaining why (e.g.,
   the API exposes no total-count endpoint).
