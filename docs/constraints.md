# Constraints — what NOT to do

## Project-specific (from the Step 1 interview)

- **No authentication.** No login, user accounts, or auth flows.
- **Backend + database are now part of the MVP stack** (was "none in the bootstrap"). A Python
  FastAPI service lives at `api/` and Postgres is the store — see
  [ADR 002](decisions/002-backend-api-on-vercel.md) / [003](decisions/003-postgres-storage.md) /
  [004](decisions/004-openrouter-ai.md). New runtime deps beyond this stack still need their own
  ADR. Secrets (`OPENROUTER_API_KEY`, `DATABASE_URL`) live only in `.env` / Vercel env vars,
  never committed and never shipped to the client.
- **No client-side routing / multi-page navigation** for now. Single board view.
- **No styling framework** (Tailwind, MUI, etc.) yet — minimal inline styles only until a
  styling approach is chosen via an ADR.

## Baseline (apply to every change)

- **No unscoped refactors.** Change only what the current spec/feature requires.
- **No new runtime dependencies without an ADR.** Ask first, record the decision, then install.
- **No code without a spec.** Every module starts with a failing `*.spec.ts(x)` test.
- **No skipping the retro.** Every feature ends with `docs/retrospectives/NNN-<slug>.md`, and
  any proposed workflow change is applied to `CLAUDE.md` / this file in the same session.
- **No governance files inside `app/`.** `CLAUDE.md`, `README.md`, and `docs/**` stay at the
  repo root.
- **App code lives in `app/` (frontend) or `api/` (backend) only.** Root-level config (dotfiles,
  CI, `vercel.json`) is fine; no other app code at the root. Governance files stay at the root.
- **No `eslint-plugin-react` until it supports ESLint 10.** The current Vite template ships
  ESLint 10; `eslint-plugin-react` is incompatible. `eslint-plugin-react-hooks` covers the
  important rules.
- **Do not loosen TypeScript strictness.** `strict`, `noImplicitAny`, `strictNullChecks`, and
  `noUncheckedIndexedAccess` stay on. Narrow types or guard values instead.
- **Do not let the dev/preview port drift.** `strictPort: true` is set; if `:5174`/`:4173` are
  taken, resolve the conflict rather than letting Vite pick another port.
- **`app/vite.config.ts` is the single source of truth for dev/preview ports.** Keep it in sync
  with `.dev-port` / `.preview-port` after any port probe — a probe that only rewrites the docs
  will leave Vite pinned to a stale port and `strictPort: true` will fail to bind.
