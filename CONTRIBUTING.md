# Contributing to Meridian

Thanks for helping improve Meridian.

## Scope

Meridian is a stack-agnostic workflow for agentic software development. Keep generic workflow assets free of product, language, framework, and hosting-specific rules. Project-specific architecture belongs in generated projects, not in this repository's templates.

## Language invariant

Meridian repository text is English-only. Keep documentation, source code, comments, identifiers, user-facing strings, tests, configuration text, and commit messages in English. The only configurable language is the agent-developer conversation language, persisted in generated projects through `LANGUAGE_POLICY.md`; an individual prompt in another language does not change it.

When changing this behavior, keep the base and governed-SDD language-policy templates identical, update both governed agent instruction files, and preserve parity between the Codex and Claude Code skills.

## Before opening a change

1. Read the relevant template, command, hook, or skill end to end.
2. Keep a change focused on one behavior or document set.
3. Preserve parity between the Codex and Claude Code governed-SDD skills when a workflow rule changes.
4. Do not change generated-project behavior accidentally while editing explanatory documentation.

## Validation

Run the repository checks before proposing a change:

```bash
python3 scripts/check_repository.py
```

The check validates JSON metadata, Bash syntax, required public-repository files, and links between the repository's Markdown documents.

For a change to a template or workflow rule, also manually trace the affected path from initialization through task creation, implementation, review, and acceptance. The templates are the product.

## Pull requests

Explain the user-facing problem, the workflow behavior that changes, and how you validated it. When a change modifies a governed-SDD rule, identify every corresponding asset you updated—for example, the workflow document, `AGENTS.md`, `CLAUDE.md`, task template, queue template, commands, and skills.

Avoid unrelated formatting changes. They make workflow changes harder to audit.
