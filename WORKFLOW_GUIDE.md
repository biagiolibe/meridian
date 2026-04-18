# 🚀 Agentic Game Development: Guida al Metodo

Questo documento è il tuo **punto di partenza**. Spiega come utilizzare questo modello per gestire lo sviluppo di un videogioco in "coppia" con agenti IA, mantenendo ordine, qualità e una visione chiara del progresso.

---

## 1. La Filosofia: "Pensa in Grande, Agisci in Piccolo"

Il segreto per far lavorare bene un'IA in progetti complessi è **isolare il contesto**.
Invece di chiedere all'agente di "aggiungere una feature", noi:
1. Definiamo la feature nel **Backlog Generale**.
2. Estraiamo un **Task Indipendente** con tutto il contesto necessario.
3. Lo diamo in pasto all'agente in una **Nuova Sessione**.

---

## 2. I Pilastri del Modello

| File | Funzione | Quando usarlo |
|------|----------|---------------|
| `PROJECT_PLAN.md` | La "Visione" e il Backlog | Quando pianifichi nuove macro-feature. |
| `TECH_DESIGN.md` | La "Bibbia" tecnica | Quando definisci l'architettura (ECS, stati, plugin). |
| `tasks/QUEUE.md` | La "Coda" di lavoro | Ogni giorno, per sapere cosa fare dopo e chi lo sta facendo. |
| `tasks/NNN-task.md` | Il "Briefing" per l'agente | Quando sei pronto a delegare un pezzo di codice specifico. |

---

## 3. Come Partire (Day 0)

1. **Copia i file**: Copia il contenuto di questa cartella nella root del tuo nuovo progetto.
2. **Inizializza il Tech Design**: Compila `TECH_DESIGN.md` definendo lo stack (es. Bevy, Rapier) e la struttura dei moduli.
3. **Inizializza il Backlog**: In `PROJECT_PLAN.md`, scrivi le macro-feature che vuoi nel gioco (es. "Sistema di inventario", "Generazione procedurale").

---

## 4. Ciclo di Lavoro Quotidiano

### Fase A: Triage & Pianificazione
Guarda `PROJECT_PLAN.md`. Qual è la prossima feature approvata?
- Se è semplice (es. "Rinomina una variabile"): fallo direttamente o scrivilo nella QUEUE come task senza file.
- Se è complessa: crea un nuovo file in `tasks/` partendo dal `TASK_BLUEPRINT.md`.

### Fase B: Preparazione del Task File
Compila il task file (`tasks/001-nome.md`). Assicurati che contenga:
- **Obiettivo**: Cosa deve cambiare?
- **Acceptance Criteria**: Come capisco se è finito?
- **Contesto Tecnico**: Incolla i pezzi di codice rilevanti o spiega esattamente dove intervenire. *L'agente non deve indovinare.*

### Fase C: Delega
Assegna il task nella `tasks/QUEUE.md` cambiando lo stato da `[ ]` a `[/]`.
Apri una nuova sessione con l'agente e chiedigli:
> *"Leggi il file `tasks/001-nome.md` ed esegui il task. Il progetto si trova in `...`."*

### Fase D: Verifica & Archiviazione
Una volta che l'agente ha finito:
1. Verifica il codice (compili? funziona?).
2. Sposta il task file in `tasks/done/`.
3. Segna come `[x]` in `QUEUE.md` e in `PROJECT_PLAN.md`.

---

## 💡 Consigli per il Successo

- **Mantieni i Task Atomici**: Se un task richiede più di 2 ore, probabilmente può essere diviso in due task più piccoli.
- **Isola i Moduli**: Più il tuo codice è modulare (Plugin, Componenti piccoli), più è facile per un agente lavorarci senza rompere il resto del gioco.
- **La Coda è Sacra**: Non iniziare 5 task contemporaneamente. Finiscine uno, archivialo, e passa al successivo.

---

*Questo modello è stato estratto dal progetto "Black Quartz" per standardizzare lo sviluppo agentico di videogiochi 2D.*
