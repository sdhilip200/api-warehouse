# Running evals (the self-grading loop)

Skills in this plugin produce real artifacts — an assessment, an `endpoints.json`, a loaded table, a validation report. An eval is a small set of **objective pass/fail checks** on one of those artifacts, plus a loop that keeps fixing the artifact until every check passes. This exists so a skill can verify its own output instead of handing you something plausible-looking but wrong.

This file defines the loop once. Each skill keeps only its own checklist in its `EVALS.md` and points here for how to run it.

## Why a separate grader

The agent that produced an artifact is a poor judge of it — it already believes the work is done, so it tends to wave its own output through. A grader with a clean context window has no such bias: it reads only the checklist and the artifact and reports what it sees. That independence is the whole point; do not grade an artifact in the same context that produced it.

## The loop

1. The skill finishes a draft of its artifact (e.g. `assess` writes `endpoints.json` + `assessment.html`).
2. Spin up a **separate grader agent** with a clean context. Give it: the skill's `EVALS.md`, the artifact(s), and nothing else.
3. The grader runs each check and returns, per check, a verdict of `pass` / `fail` / `skipped` with one line of evidence. `skipped` is for a check that genuinely cannot be computed (the honesty rule — see [anti-slop.md](anti-slop.md) and the project honesty rule); never let a grader invent a `pass`.
4. If every check is `pass` or `skipped`, stop — the artifact is good.
5. If any check is `fail`, hand the failures back to the original skill agent, which revises the artifact, then go to step 2.
6. Cap the loop at **5 rounds**. If checks still fail after 5 rounds, stop and report the remaining failures plainly rather than looping forever — a stuck check usually means the API (or the user's intent) genuinely can't satisfy it, which is information the user needs.

## Writing good checks

A check earns its place only if it can fail for a real reason. Aim for checks that are:

- **Objective** — "the report shows an incremental verdict with evidence", not "the report is high quality".
- **Artifact-grounded** — checkable by reading the file, not by re-interviewing the user.
- **Honest about gaps** — if a check depends on data the API doesn't expose, it returns `skipped`, not `fail`.

Keep each skill's checklist short (5–10 checks). A long checklist of checks that always pass tells you nothing and slows every run.

## Note for contributors

When you add a check to a skill's `EVALS.md`, ask: could this ever fail on a correct artifact? If yes, it's a flaky check — tighten it. Could it ever pass on a broken artifact? If yes, it's too loose — make it specific.
