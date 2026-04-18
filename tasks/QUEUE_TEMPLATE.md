# Task Execution Queue

Questa è la coda di esecuzione operativa. I task sono ordinati per priorità.

## Come usare questa coda

- **Esecuzione**: Prendi il primo task `[ ]` disponibile.
- **Aggiornamento**: Cambia `[ ]` in `[/]` quando inizi e in `[x]` quando finisci.
- **Delega**: Segui le istruzioni "Come delegare" nel task file.
- **Archiviazione**: A task completato, sposta il file in `tasks/done/`.

## Priorità

| Codice | Significato |
|--------|-------------|
| 🔴 P1  | Bloccante / Critico |
| 🟡 P2  | Feature importante |
| 🟢 P3  | Ottimizzazione / Polish |

---

## 🤖 Come delegare un task a un agente

### Antigravity (IA locale)
Apri una nuova chat e scrivi:
> *"Leggi il file `tasks/NNN-nome.md` ed esegui il task. Il progetto si trova in `...`."*

### Claude CLI
```bash
claude "$(cat tasks/NNN-nome.md)"$'\n\nEsegui questo task nel progetto corrente.'
```

---

## 🏃 Coda Attiva

| Stato | ID | Titolo | Priorità | Agente | Task File |
|-------|----|--------|----------|--------|-----------|
| `[/]` | 001 | Esempio: Inizializzare ECS | 🔴 P1 | Antigravity | [001](001-init-ecs.md) |
| `[ ]` | 002 | Esempio: Creare spawner | 🟡 P2 | — | [002](002-spawner.md) |

---

## 🧪 Task Rapidi (Senza File)

Task che richiedono < 15 min e non necessitano di briefing dettagliato.

| Stato | Descrizione | Priorità |
|-------|-------------|----------|
| `[ ]` | Pulizia import | 🟢 P3 |

---

## ✅ Archiviati (Completati)

| Stato | ID | Titolo | Agente | File |
|-------|----|--------|--------|------|
| `[x]` | 000 | Definizione architettura | Manuale | [000](done/000-arch.md) |

---

*Ultimo aggiornamento: [Data]*
