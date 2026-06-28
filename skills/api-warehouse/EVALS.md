# EVALS — api-warehouse orchestrator

Run these checks after a full end-to-end execution. Spin up a grader agent
with a clean context; give it this file and the run transcript. See
[`../../references/running-evals.md`](../../references/running-evals.md) for
the grading loop.

| # | Check | How to verify | Expected |
|---|-------|---------------|----------|
| 1 | Step order honored | Transcript shows connect → assess → land → validate → schedule with no step skipped or out of sequence | pass / fail |
| 2 | CHECKPOINT pause occurred before land | Transcript shows orchestrator stopped after assess, presented assessment.html to user, and waited for explicit confirmation before invoking land | pass / fail |
| 3 | Each step ran its own eval loop | Transcript contains a grader-agent invocation (separate context) for each of the five steps | pass / fail / skipped if step was skipped by user |
| 4 | Scope guard respected | No transformation, renaming, or modelling operations appear in the land step output or the loaded table schema | pass / fail |
| 5 | No secret values leaked | API tokens, passwords, and connection strings do not appear as literal values anywhere in the transcript or generated files | pass / fail |
| 6 | Validation passed before schedule ran | The validate report shows all checks pass (or explicitly skipped) before the schedule step was invoked | pass / fail / skipped if schedule was not reached |
| 7 | MEMORY.md updated | If a notable run quirk occurred, a new entry was appended to MEMORY.md recording it; verify the transcript shows MEMORY.md was consulted and written. If no quirks occurred, this check is `skipped`. | pass / fail / skipped if no quirks occurred |
