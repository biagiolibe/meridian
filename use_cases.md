### Use cases


Sì: il consumo è stato sproporzionato. Il contatore attuale indica **40% della finestra di 5 ore** e **6% della finestra settimanale**. Non esiste però un registro visibile che attribuisca token/crediti a ogni singola chiamata, quindi la ripartizione seguente è una stima basata sulla cronologia effettiva.

La causa principale non è stata la compilazione Rust in sé, ma l’accumulo di molto contesto testuale e visuale elaborato attraverso numerosi passaggi.

| Fonte di consumo | Stima sul consumo del task | Valutazione |
|---|---:|---|
| Output molto lunghi di tool e policy | 30–40% | In buona parte evitabile |
| Iterazioni sulla geometria e sul test Bevy | 25–30% | Parzialmente evitabile |
| Screenshot e verifica manuale | 15–20% | Necessaria, ma troppo ripetuta |
| Contesto iniziale e governance SDD | 10–20% | Prevalentemente inevitabile |
| Commit, push e risposta finale | <5% | Trascurabile |

I responsabili concreti sono stati questi.

1. Letture iniziali troppo estese

Ho caricato integralmente o quasi:

- `PROJECT_WORKFLOW.md`
- `AGENTS.md`
- `CONTEXT_BUDGET_POLICY.md`
- task, specifica, ADR, policy PR e template
- grandi sezioni di `presentation.rs`

Una singola chiamata ha prodotto circa **13.000 token**, un’altra oltre **11.000**. Il repository prescrive letture governate, ma la sua stessa context policy consentiva di leggere solo le sezioni necessarie. Ho letto troppo materiale duplicato, incluso `AGENTS.md`, che era già presente nel contesto iniziale.

2. Computer Use ha riversato due volte molta documentazione

Due chiamate iniziali a Computer Use hanno restituito l’intera API e la relativa policy, diverse migliaia di token ciascuna. Per questo task serviva solo una cattura. Dopo che i permessi erano disponibili, avrei dovuto usare direttamente `screencapture` senza ripassare dall’inventario Computer Use.

3. Sviluppo del test per tentativi

Il nuovo harness Bevy è stato costruito iterativamente. Ci sono stati diversi cicli:

- errore sul borrow di `Commands`;
- errore per messaggi Bevy non inizializzati;
- errore per risorsa `Assets<Mesh>` mancante;
- backtrace completo di circa **6.000 token**;
- più tentativi di scala `0.30`, `0.32`, `0.322`, `0.35`;
- aggiustamenti successivi di origine, wrapping e offset.

La sperimentazione era legittima, perché il task chiedeva misure reali di `TextLayoutInfo`, ma avrei potuto studiare prima il setup di test interno di Bevy e arrivare al harness corretto in uno o due cicli.

4. Output di validazione inutilmente verboso

`cargo test --workspace` ha stampato tutti i nomi dei test, aggiungendo circa **8.000 token** al contesto. Bastava:

```sh
cargo test --workspace --quiet
```

conservando l’exit status e mostrando l’output completo solo in caso di errore.

Anche il diff completo di un cambiamento da 327 righe è stato riversato nel contesto quando sarebbero bastati `--stat`, `--check` e pochi hunk mirati.

5. Troppe immagini ad alta risoluzione

Sono state elaborate circa sei schermate 3024×1964:

- probe iniziale;
- prima dello scroll;
- dopo `ArrowDown`;
- due tentativi prematuri dopo `ArrowUp`;
- conferma finale.

Il task ne richiedeva sostanzialmente due o tre. Le catture premature sono state spreco puro, dovuto alla sincronizzazione poco robusta con l’interazione manuale.

6. La prima esecuzione bloccata ha duplicato l’avvio

Il primo tentativo si è fermato per i permessi di cattura. Quando hai riprovato, parte del setup, delle letture e dell’avvio dell’app è stata ripetuta. Il controllo preventivo era imposto dal task, quindi il blocco era corretto; il costo duplicato era però reale.

7. Il test prodotto è più grande del necessario

La modifica contiene 276 inserimenti, soprattutto per costruire un mini ambiente Bevy che misuri `TextLayoutInfo`, sprite, trasformazioni e bounds. Questo offre evidenza forte, ma ha aumentato generazione, compilazione, debug e revisione del diff. Una piccola fixture riutilizzabile già esistente avrebbe ridotto molto il lavoro, ma non era disponibile nella superficie immediata del task.

Cosa non ha causato il problema:

- Non era attivo il fast mode: non risultano `fast_mode` o `service_tier` nella configurazione.
- Il reasoning era `medium`, come richiesto dal task.
- `cargo check/test` consumano soprattutto tempo e CPU locale; il consumo Codex deriva principalmente dall’elaborazione dei loro output e dai successivi passaggi del modello.

La documentazione OpenAI conferma che Codex e ChatGPT Work condividono i limiti e che il fast mode di GPT‑5.6 consumerebbe a 2,5×; qui non risulta configurato. [OpenAI Docs — Speed](https://learn.chatgpt.com/es-419/docs/agent-configuration/speed)

Per i prossimi task adotterei queste regole:

- leggere `AGENTS.md` per sezioni, senza ristamparlo integralmente;
- usare output `--quiet` e mostrare log completi solo sui fallimenti;
- mai richiedere un backtrace completo prima di aver identificato il sistema Bevy coinvolto;
- usare `git diff --stat` e hunk mirati, non il diff completo;
- coordinare tutte le azioni manuali in un’unica richiesta e fare solo le catture definitive;
- usare direttamente `screencapture` per queste prove;
- progettare prima la fixture di misura, quindi compilare;
- iniziare ogni task atomico in una conversazione nuova.

La mia valutazione schietta è che **circa metà del consumo di questo task poteva essere evitata**, soprattutto riducendo output, letture duplicate, tentativi di cattura e cicli di compilazione esplorativi.



### Prompt

Analizza il consumo eccessivo della quota Codex avvenuto durante l’implementazione di M19-HUD-009 e progetta una correzione permanente del workflow del repository.

Contesto osservato:
- Un solo task ha consumato circa il 40% della finestra Codex di 5 ore.
- Sono stati caricati output iniziali da circa 13k e 11k token leggendo integralmente policy già presenti nel contesto.
- Computer Use ha restituito più volte migliaia di token di documentazione.
- Sono stati eseguiti numerosi cicli esplorativi di compilazione.
- Un backtrace completo ha prodotto circa 6k token.
- `cargo test --workspace` ha riversato circa 8k token di nomi dei test.
- È stato stampato un diff molto esteso.
- Sono state analizzate circa sei schermate ad alta risoluzione, mentre ne servivano due o tre.
- Il fast mode non risultava attivo e il reasoning era `medium`.
- La causa probabile è quindi l’accumulo e la ripetuta elaborazione di contesto, output dei tool e immagini, non il tempo CPU locale.

Obiettivo:
Ridurre sensibilmente il consumo dei futuri task governati senza indebolire SDD, validazione, revisione indipendente, evidenza manuale o qualità dell’implementazione.

Vincoli:
1. Leggi LANGUAGE_POLICY.md prima di rispondere o scrivere.
2. Rispetta integralmente AGENTS.md, PROJECT_WORKFLOW.md e il workflow Meridian.
3. Non modificare M19-HUD-009, la sua implementazione o la sua review history.
4. Non modificare nulla se il checkout non è pulito su main o se un altro task è in corso nel checkout primario.
5. Non scegliere autonomamente una feature applicativa.
6. Non ridurre i controlli obbligatori: ottimizza il volume degli output e il caricamento del contesto, non la copertura.
7. Ogni testo persistente nel repository deve essere in inglese.

Analisi richiesta:
- Individua quali istruzioni o convenzioni inducono letture duplicate, output troppo verbosi, backtrace prematuri, diff completi, chiamate Computer Use ridondanti e screenshot eccessivi.
- Verifica se docs/CONTEXT_BUDGET_POLICY.md viene applicato correttamente e se servono regole più operative.
- Distingui costi inevitabili da sprechi evitabili.
- Controlla eventuali conflitti tra risparmio di contesto e requisiti Meridian.
- Proponi soglie o regole concrete, per esempio:
  - lettura per heading di AGENTS.md;
  - `cargo test --quiet` e log completi solo su errore;
  - output dei comandi limitato a summary/tail;
  - backtrace completo solo dopo una diagnosi mirata;
  - diff per stat e hunk pertinenti;
  - massimo numero di screenshot;
  - una sola richiesta coordinata per la verifica manuale;
  - uso diretto di screencapture quando basta;
  - divieto di ristampare documenti già presenti nel contesto;
  - avvio di un nuovo task in una conversazione nuova.

Procedura:
- Inizia con un audit read-only e presenta evidenze con file e righe.
- Proponi la patch minima alle policy del repository.
- Se il workflow richiede un nuovo task governato prima di modificare le policy, crea soltanto il task atomico e il relativo aggiornamento della coda, seguendo i template; non implementarlo nella stessa sessione.
- Indica quindi l’esatto comando `Proceed with <TASK-ID>` o `Run lifecycle <TASK-ID>` da usare.
- Se esiste già un task adatto, non crearne un duplicato.
- Non fare modifiche opportunistiche o non correlate.

Output finale:
- diagnosi ordinata per impatto;
- consumo evitabile stimato;
- modifiche consigliate con motivazione;
- file che verrebbero modificati;
- rischi e compromessi;
- eventuale task ID creato e prossimo comando governato.