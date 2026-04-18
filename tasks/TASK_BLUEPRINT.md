# Task [ID] — [Titolo del Task]

> **ID**: `[NNN]`
> **Categoria**: [Architettura / Mappa / Giocatore / etc.]
> **Priorità**: [🔴 P1 / 🟡 P2 / 🟢 P3]
> **Stima**: [~1h / ~2h / etc.]
> **Assegnato a**: [Antigravity / Claude CLI / non assegnato]
> **Sessione**: [ID conversazione o riferimento temporale]

---

## 🎯 Obiettivo

[Cosa deve essere fatto?]
[Perché è necessario?]

---

## 📋 Acceptance Criteria

[Un task è considerato completato quando:]
- [ ] Il codice compila senza warning.
- [ ] La feature X funziona come descritto.
- [ ] [Aggiungere criteri specifici...]

---

## 📁 File Rilevanti

| File | Ruolo |
|------|-------|
| `src/modulo/mod.rs` | Caricamento del plugin e definizione sistemi. |
| `src/modulo/components.rs` | Struttura dei dati ECS. |

---

## 🧩 Contesto Tecnico

[Incolla qui le definizioni di struct o enum coinvolte, o descrivi lo stato attuale del codice.]

- **Comportamento attuale**: [Cosa succede ora?]
- **Comportamento desiderato**: [Cosa deve succedere dopo?]

---

## 🔨 Implementazione Suggerita

[Passaggi consigliati per l'agente IA]

1. [Passo 1]
2. [Passo 2]

```rust
// Eventuale snippet di esempio
```

---

## ⚠️ Vincoli e Attenzioni

- **Bevy [Versione]**: Assicurarsi di usare le API corrette per questa versione.
- **Performance**: [Evitare loop pesanti, etc.]
- **Stile**: Seguire le convenzioni del progetto definite nel `TECH_DESIGN.md`.

---

## 🔗 Dipendenze

- **Dipende da**: [ID task precedente o nessuno]
- **Blocca**: [ID task successivo o nessuno]

---

## 🤖 Come delegare questo task a un agente

### Opzione A — Antigravity (Nuova Chat)
Copia e incolla:
> *"Leggi il file `tasks/[NNN]-nome.md` ed esegui il task. Il progetto si trova in `/path/to/tuo/progetto/`."*

### Opzione B — Claude CLI
Esegui nel terminale:
```bash
claude "$(cat tasks/[NNN]-nome.md)"$'\n\nEsegui questo task nel progetto.'
```
