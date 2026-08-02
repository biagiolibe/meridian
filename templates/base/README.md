# [Project Name]

[Descrizione breve del progetto in una o due frasi.]

## Getting Started

```bash
# [comandi per buildare/eseguire/testare il progetto]
```

[Se il toolchain è pinnato (es. rust-toolchain.toml, .nvmrc, pyproject.toml), menzionarlo qui.]

## Repository & Claude Code Configuration

Note per replicare il setup di lavoro su un'altra macchina.

**Toolchain**
- [linguaggio/runtime e versione pinnata]
- Dipendenze chiave: [elenco]

**Claude Code — file di repo (tracciati in git)**
- `CLAUDE.md` — convenzioni di progetto, invarianti e workflow Meridian.
- `.claudeignore` — tiene fuori dal contesto di Claude build artifact e file non-sorgente.
- `.gitignore` — esclude output di build, cruft OS ed editor config.

**Claude Code — impostazioni di sessione (non salvate nel repo, da reimpostare per macchina/sessione)**
- Modello: **[nome modello]**
- Advisor: **[nome advisor]**
- Effort level: **[livello]**

Reimpostarle con `/model`, `/advisor` e `/effort` dopo il clone su una macchina nuova.

**Non tracciato in git (locale alla macchina)**
- `.claude/settings.local.json` — allowlist dei permessi locale; si rigenera con i prompt di approvazione.
- `.vscode/` / `.idea/` — config specifica dell'editor.

---

*Ultimo aggiornamento: [Data]*
