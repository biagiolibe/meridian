# Concise Completion Report

Use this handoff after validation. Keep it short and make every deviation explicit.

```md
## Completion Report — <TASK-ID>

- Files changed: `<paths>`
- Branch: `<task-branch>`
- Implementation commit: `<commit SHA>`
- Base `main` commit: `<commit SHA>`
- Validation: `<exact commands run with their exit status, or the CI check run and its conclusion for this exact commit — not a bare "passed">`
- Manual verification: `<none | screenshot path — view checked — result>`
- Acceptance criteria: `<all met | list criterion IDs/status>`
- Budget usage: `<diagnostics used/cap; captures used/cap by criterion; context expansions used/cap>`
- Blockers/deviations: `<none | concrete issue, scope expansion, or context expansion and reason>`
```

Do not claim completion when validation fails or an acceptance criterion is unresolved. For reviews, retain the same four fields in `tasks/reviews/<TASK-ID>.md` and add the required verdict from `docs/CODE_REVIEW_PROMPT.md`. For `CHANGES_REQUESTED`, name that review-record path and its local handoff commit in the concise chat report; the record itself remains the canonical evidence.

<!-- MERIDIAN:BEGIN capability=manual-verification-record v1 -->
When the task declares `Manual verification: required`, name the screenshot
path, the view checked, and the result (pass/fail) — a reviewer must be able
to use it without reconstructing the session. When the task declares
`Manual verification: none`, state that explicitly rather than omitting the
field.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=ci-verified-validation v1 -->
Report validation as falsifiable evidence, not an assertion: a self-reported
"tests passed" is exactly the claim an independent reviewer exists to verify,
not to repeat back. Name the exact command(s) actually run and their exit
status (or the CI check run for this commit), so a reviewer can decide,
per `docs/PULL_REQUEST_POLICY.md`, whether to trust an independent CI result
or perform its own scoped validation.
<!-- MERIDIAN:END -->
