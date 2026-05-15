# Task Execution Queue

Questa è la coda di esecuzione operativa. I task sono ordinati per priorità.

## Come usare questa coda

- **Esecuzione**: Prendi il primo task `[ ]` disponibile.
- **Aggiornamento**: Cambia `[ ]` in `[/]` quando inizi e in `[x]` quando finisci.
- **Archiviazione**: A task completato, sposta il file in `tasks/done/`.

## Priorità

| Codice | Significato |
|--------|-------------|
| 🔴 P1  | Bloccante / Critico |
| 🟡 P2  | Feature importante |
| 🟢 P3  | Ottimizzazione / Polish |

---

## 🤖 Come delegare un task a Claude CLI

```bash
claude "$(cat tasks/NNN-nome.md)"$'\n\nEsegui questo task nel progetto corrente.'
```

---

## 🏃 Coda Attiva

| Stato | ID | Titolo | Priorità | Agente | Task File |
|-------|----|--------|----------|--------|-----------|
| `[ ]` | 001 | Setup iniziale | 🔴 P1 | — | [001](001-setup.md) |

---

## 🧪 Task Rapidi (Senza File)

Task che richiedono < 15 min e non necessitano di briefing dettagliato.

| Stato | Descrizione | Priorità |
|-------|-------------|----------|
| `[ ]` | *(nessuno)* | — |

---

## ✅ Archiviati (Completati)

| Stato | ID | Titolo | Agente | File |
|-------|----|--------|--------|------|

---

*Ultimo aggiornamento: [Data]*
