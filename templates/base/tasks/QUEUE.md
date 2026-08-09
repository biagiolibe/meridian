# Task Execution Queue

Questa è la coda di esecuzione operativa. I task sono ordinati per priorità.

Le fasi/sezioni interamente chiuse (tutte `[x]`) vivono in
`tasks/QUEUE_ARCHIVE.md`, non qui — questo file traccia solo lavoro con
qualcosa ancora aperto, per tenere basso il costo di lettura a ogni
sessione. Consulta l'archivio solo quando serve la storia/motivazione di
una fase passata.

## Come usare questa coda

- **Esecuzione**: Prendi il primo task `[ ]` disponibile.
- **Aggiornamento**: Cambia `[ ]` in `[/]` quando inizi e in `[x]` quando finisci.
- **Archiviazione file task**: A task completato, sposta il file in `tasks/done/`.
- **Archiviazione coda**: Quando un'intera fase/sezione della Coda Attiva diventa `[x]`, sposta le sue righe in `tasks/QUEUE_ARCHIVE.md` (crealo se non esiste, riusando la stessa struttura a tabella di questo file) invece di lasciarle accumulare qui. Non aspettare che il file diventi enorme — archivia appena una fase si chiude.

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
