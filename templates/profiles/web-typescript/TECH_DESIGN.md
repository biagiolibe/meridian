# Technical Design Document — [Project Name]

Questo documento descrive l'architettura tecnica e le scelte implementative del progetto.

## 1. Stack Tecnologico

- **Linguaggio**: TypeScript (strict mode)
- **Framework**: [React / Next.js / Express / Fastify]
- **Styling**: [Tailwind CSS / CSS Modules / Styled Components]
- **State Management**: [Zustand / Redux / React Query]
- **Database/API**: [PostgreSQL + Prisma / Supabase / REST API / tRPC]
- **Testing**: [Vitest / Jest + React Testing Library / Playwright]
- **Bundler**: [Vite / Next.js / esbuild]

---

## 2. Struttura del Progetto

```
src/
  components/    # Componenti UI riutilizzabili
  features/      # Moduli per feature specifiche (ogni feature = cartella autonoma)
  hooks/         # Custom React hooks condivisi
  lib/           # Utility, helpers, configurazioni client
  types/         # Tipi TypeScript globali
  api/           # Route handlers / server-side logic
```

---

## 3. Architettura & Pattern

### Feature-first structure
Ogni feature vive nella propria cartella (`features/auth/`, `features/dashboard/`) con componenti, hooks, e tipi locali. Si esporta solo l'interfaccia pubblica da `index.ts`.

### Gestione dati
[Descrivi il pattern: Server Components / Client Components / SWR / React Query]

### Routing
[Descrivi la struttura delle route: file-based (Next.js) / React Router / etc.]

---

## 4. Convenzioni di Sviluppo

### Componenti
- Un componente per file, nome = nome file (PascalCase).
- Props sempre tipizzate con interfacce esplicite (no `any`).

### Naming
- File componenti: `PascalCase.tsx`
- Hook: `useCamelCase.ts`
- Utility: `camelCase.ts`
- Tipi/interfacce: `PascalCase` (no prefisso `I`)

### Gestione degli Errori
- Usare Error Boundaries per errori UI.
- API calls: gestire loading/error/success states esplicitamente.

---

## 5. Decisioni Architetturali

### [Decisione A]
**Contesto**: [Perché è stato necessario scegliere]
**Scelta**: [Cosa è stato scelto]
**Motivazione**: [Perché questa scelta]

---

*Ultima revisione: [Data]*
