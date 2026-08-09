# Task Execution Queue

Questa è la coda di esecuzione operativa. I task sono ordinati per priorità.

Le fasi/sezioni interamente chiuse (tutte `[x]`) vivono in
[`QUEUE_ARCHIVE.md`](QUEUE_ARCHIVE.md), non qui — questo file traccia solo
lavoro con qualcosa ancora aperto, per tenere basso il costo di lettura a
ogni sessione. Consulta l'archivio solo quando serve la storia/motivazione
di una fase passata.

## Come usare questa coda

- **Esecuzione**: Prendi il primo task `[ ]` disponibile.
- **Aggiornamento**: Cambia `[ ]` in `[/]` quando inizi e in `[x]` quando finisci.
- **Delega**: Segui le istruzioni "Come delegare" nel task file.
- **Archiviazione file task**: A task completato, sposta il file in `tasks/done/`.
- **Archiviazione coda**: Quando un'intera fase/sezione della Coda Attiva diventa `[x]`, sposta le sue righe in `tasks/QUEUE_ARCHIVE.md` (crealo se non esiste, riusando la struttura di questo file) invece di lasciarle accumulare qui. Non aspettare che il file diventi enorme — archivia appena una fase si chiude.

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

Tieni qui solo i completati recenti/rilevanti al lavoro attivo. Quando
questa sezione (o un'intera fase della Coda Attiva) è chiusa e non serve
più come riferimento immediato, spostala in `tasks/QUEUE_ARCHIVE.md`.

| Stato | ID | Titolo | Agente | File |
|-------|----|--------|--------|------|
| `[x]` | 000 | Definizione architettura | Manuale | [000](done/000-arch.md) |

---

*Ultimo aggiornamento: [Data]*
