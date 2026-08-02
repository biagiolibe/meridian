# [Project Name]

[Descrizione breve del progetto in una o due frasi.]

## Commands

```bash
# [comandi principali: run, test, lint, format]
```

## Documents

| File | Contents |
|---|---|
| `TECH_DESIGN.md` | Architettura, convenzioni, decisioni tecniche. |
| `tasks/QUEUE.md` | **Cosa fare ora.** |

## Conventions

- [Convenzioni di codice/documentazione specifiche del progetto.]
- [Invarianti architetturali da non violare.]

## Workflow (Meridian)

Un task alla volta. Al completamento di un task:

1. verifica gli acceptance criteria nel file del task;
2. sposta il file da `tasks/` a `tasks/done/`;
3. aggiorna lo stato a `[x]` in `tasks/QUEUE.md` e in `PROJECT_PLAN.md`.

## Approach

- Read existing files before writing. Don't re-read unless changed.
- Thorough in reasoning, concise in output.
- Skip files over 100KB unless required.
- No sycophantic openers or closing fluff.
