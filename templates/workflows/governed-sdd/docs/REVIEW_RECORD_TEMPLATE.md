# Review Record

Use one durable review record per required-review task at
`tasks/reviews/<TASK-ID>.md`. It is the canonical handoff from reviewer to
implementer; chat output may summarize it but must not be the only location of
findings. Create the directory when the first record is needed.

The reviewer creates or appends an attempt for every `CHANGES_REQUESTED` and
`APPROVE` verdict. Findings must be actionable, prioritized, and tied to
evidence. The implementer marks each requested change as resolved in the next
attempt before returning the task to review. Do not edit a prior reviewer's
findings or evidence; append a new attempt instead.

```md
# Review Record — <TASK-ID>

## Attempt <N> — <CHANGES_REQUESTED | APPROVE | BLOCKED>

- Reviewed commit: `<commit SHA>`
- Base `main` commit: `<commit SHA>`
- Reviewer evidence: `<commands, diff, and task sources inspected>`
- Validation observed: `<commands and pass/fail result>`

### Findings

- [ ] P1 — `<required change>`
  - Evidence: `<path:line, command output, or acceptance-criterion reference>`

### Resolution (implementer; omit until remediation)

- [x] P1 — `<what changed and where>`
  - Evidence: `<commit, path:line, or validation result>`

### Blockers/deviations

`<none | concrete issue>`
```

Use `- [ ]` only for changes that must be made before approval. `P0` and `P1`
findings block approval; `P2` findings are included only when they require a
bounded change in this task. Style-only commentary does not belong in the
record.
