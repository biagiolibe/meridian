# Technical Design Document — [Nome del Gioco]

Questo documento descrive l'architettura tecnica e le scelte implementative del progetto.

## 1. Stack Tecnologico

- **Linguaggio**: Rust (Edizione 2021)
- **Engine**: Bevy (Versione [X.Y])
- **Fisica**: [bevy_rapier2d / nessuno]
- **Librerie Chiave**: [es. noise, rand, bevy_asset_loader]

---

## 2. Stati del Gioco (`GameState`)

Descrizione degli stati principali gestiti tramite Bevy States:

- `Loading`: Caricamento asset.
- `MainMenu`: Interfaccia iniziale.
- `Playing`: Ciclo di gioco principale.
- [Aggiungere altri stati...]

---

## 3. Architettura ECS & Moduli

### Struttura dei Plugin
Ogni modulo deve avere il proprio `Plugin` per incapsulare i sistemi.

- `game`: Gestione stati e configurazioni globali.
- `player`: Componenti e logiche del giocatore.
- `level`: Caricamento e gestione della mappa.
- [Aggiungere altri moduli...]

### Ordinamento dei Sistemi (`SystemSets`)
L'ordine di esecuzione garantito è:
`SetA` → `SetB` → `SetC` ...

---

## 4. Convenzioni di Sviluppo

### Gestione degli Eventi
Usare gli eventi Bevy per disaccoppiare i moduli (es. `PlayerHitEvent` emesso in `physics` e letto in `ui`).

### FixedUpdate vs Update
- Usare `FixedUpdate` per tutto ciò che riguarda la fisica e le meccaniche di gioco core (movimento, collisioni).
- Usare `Update` per animazioni visive e UI.

### Inserimento Asset
Usare un sistema di caricamento centralizzato (es. una risorsa `GameAssets`) per evitare di caricare file multipli nei sistemi.

---

## 5. Meccaniche Core (Dettagli)

### [Meccanica A]
Descrizione tecnica di come funziona...

### [Meccanica B]
Descrizione tecnica di come funziona...

---

*Ultima revisione: [Data]*
