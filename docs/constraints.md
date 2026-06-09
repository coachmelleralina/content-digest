# Constraints — what NOT to do

## Project-specific (from the Step 1 interview)

- **No authentication.** No login, user accounts, or auth flows.
- **No backend or database in the bootstrap.** Article extraction and AI summarization are
  deferred features; each must be specced in `docs/requirements/feature-*.md` with its own
  preflight (extraction service / API key) and an ADR before any runtime dependency is added.
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
- **No app code outside `app/`.** Root-level config (dotfiles, CI) is fine; app code is not.
- **No `eslint-plugin-react` until it supports ESLint 10.** The current Vite template ships
  ESLint 10; `eslint-plugin-react` is incompatible. `eslint-plugin-react-hooks` covers the
  important rules.
- **Do not loosen TypeScript strictness.** `strict`, `noImplicitAny`, `strictNullChecks`, and
  `noUncheckedIndexedAccess` stay on. Narrow types or guard values instead.
- **Do not let the dev/preview port drift.** `strictPort: true` is set; if `:5173`/`:4173` are
  taken, resolve the conflict rather than letting Vite pick another port.
