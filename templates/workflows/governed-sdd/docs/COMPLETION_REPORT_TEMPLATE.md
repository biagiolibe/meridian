# Concise Completion Report

Use this handoff after validation. Keep it short and make every deviation explicit.
Save it at `tasks/handoffs/<TASK-ID>.md`; `meridian execution handoff-check`
and `ready-check` use that canonical path when no report path is supplied.

```md
## Completion Report — <TASK-ID>

- Files changed: `<paths>`
<!-- MERIDIAN:BEGIN capability=task-worktree-handoff v4 -->
- Branch: `<task-branch>`
- Worktree: `<task-worktree path relative to the worktree root, as returned in handoff_worktree; never an absolute path>`
- Implementation commit: `<commit SHA, or the descriptive form below>`
- Validated task commit: `<commit SHA covered by all validation evidence, or the descriptive form below>`
- Validated base `main` commit: `<commit SHA from which the task worktree was created>`
- Current task commit: `<task branch HEAD SHA; validated task commit must be its ancestor and the intervening diff must contain only permitted lifecycle records, or the descriptive form below>`
- Integration requirement: `<bounded gate | full combined-tree validation with reason>`
- Declared integration surface: `<files/directories; dependencies; generated/configuration inputs; schemas; shared-governance records; behavioral surfaces, or explicit none for each category>`

When this report is committed in the implementation commit, that commit cannot
name itself. The implementation, validated task, and current task commit fields
may therefore use a descriptive form that identifies the commit by subject and
branch, for example `the task commit <subject> (created after this report; see
git log -1 <task-branch>)`; the latter two fields may say `same as the
implementation commit`. When a later lifecycle-only commit corrects or extends
the report, name every earlier commit by full SHA and describe only the new
commit. The current task commit always identifies task branch `HEAD`; never
record the validated base `main` commit or any other commit in that field. To
correct a wrong commit field, create a new lifecycle-only commit changing only
the handoff record, push the task branch once, then begin the next review
attempt. Amend and force-push remain prohibited.
<!-- MERIDIAN:END -->
- Validation: `<exact commands run with their exit status, or the CI check run and its conclusion for this exact commit — not a bare "passed">`
- Manual verification: `<none | screenshot path — view checked — result>`
- Acceptance criteria: `<all met | list criterion IDs/status>`
- Budget usage: `<diagnostics used/cap; captures used/cap by criterion; context expansions used/cap; investigation scope used/cap>`
- Isolated exploration: `<none | question(s) recorded through meridian execution investigate>`
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
