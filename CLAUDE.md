# content-digest

Paste an article link → the app extracts the text, an AI step produces a short summary, key
points, and tags, and suggests a category; the result lands as a card on a board with
topic-based sections. This repo follows **agentic engineering** (spec-first, decisions
recorded, retros that improve the workflow), with the governance layer physically separated
from the application code.

## Repository layout

```
content-digest/
  CLAUDE.md        ← this file: entry point for Claude (root, never inside app/)
  README.md        ← entry point for humans
  package.json     ← root pass-through scripts (npm run dev/build/test/lint/format)
  .gitignore .editorconfig .nvmrc .env.example
  docs/            ← requirements / decisions / retrospectives / constraints
  app/             ← ALL Vite + React + TypeScript code lives here
```

Governance (`CLAUDE.md`, `README.md`, `docs/**`) lives at the root and never inside `app/`.
App code lives under `app/` and never at the root. See ADR
[001-agent-structure](docs/decisions/001-agent-structure.md).

## How to work in this repo (working agreement)

1. No code without a spec. Every feature begins as a file under `docs/requirements/` (at repo
   root) and a failing test under `app/src/**/*.spec.ts(x)`.
2. No architectural choice without an ADR under `docs/decisions/`.
3. Read [docs/constraints.md](docs/constraints.md) before proposing anything new. Surface
   conflicts, don't silently comply.
4. The loop is: spec → failing test → minimal code → green test → commit. One concern per
   commit.
5. Logic in pure modules, rendering in components. Specs target the logic. Add a DOM-testing
   layer (e.g. React Testing Library) only via an ADR when a real need appears.
6. When in doubt, ask. Use AskUserQuestion rather than guessing requirements.
7. Keep this file's "Current state" section updated after every merged change.
8. Dev server lives at `http://127.0.0.1:<DEV_PORT>/` where `DEV_PORT` is recorded in
   `.dev-port` (defaults to 5174, probed for a free port at bootstrap time). Always read the
   current port from `.dev-port` instead of hardcoding 5174. `strictPort: true` is set so Vite
   never silently drifts.
9. **Retrospective after every feature.** Once a feature is green and committed, write
   `docs/retrospectives/NNN-<slug>.md` capturing what worked, what didn't, and concrete
   workflow changes. If the retro proposes a change, **edit `CLAUDE.md` (working agreement,
   constraints, or links) in the same session** — don't defer. Add a new ADR if the change is
   architectural. Then update the "Self-improvement log" section below to link the new retro.
   Commit as `chore(retro): NNN-<slug>`.
10. **Layout discipline.** Governance files live at the repo root and never inside `app/`. App
    code lives inside `app/` and never at the repo root. Root-level config (CI, dotfiles) is
    allowed; app code at root is not.
11. **Conventional Commits.** Format: `<type>(<scope>): <subject>`. Types: `feat`, `fix`,
    `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`. Retros are committed
    as `chore(retro): NNN-<slug>`. ADR additions as `docs(adr): NNN-<slug>`.
11b. **Pull-Request flow (ADR 005).** Never merge to `main` locally. Each task/agent: branch →
    push → open a PR against `main` → wait for the green `frontend` + `backend` CI checks →
    squash-merge → delete the branch. `main` is protected (PR required, checks must pass). See
    [ADR 005](docs/decisions/005-github-flow-ci-branch-protection.md).
12. **CLAUDE.md ≤ ~200 lines.** It is a router, not an encyclopedia. If a retro update would
    push it past ~200 lines, move detail into a linked file under `docs/` and link from here
    instead. Same applies to `constraints.md` — split into topical files once over ~150 lines.

## Documentation TOC

- [docs/requirements/overview.md](docs/requirements/overview.md) — goal, user, success criteria
- [docs/PRD.md](docs/PRD.md) — product requirements (problem, scope, MVP success criteria)
- [docs/PLAN.md](docs/PLAN.md) — MVP build plan (stack, folder structure, build steps)
- [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md) — prioritized hardening/refactor backlog (post-v2)
- [docs/requirements/](docs/requirements/) — one `feature-NNN-*.md` per feature (001–019)
- [docs/decisions/](docs/decisions/) — ADRs: 001 root-vs-`app/`, 002 Vercel backend, 003
  Postgres, 004 OpenRouter, 005 GitHub Flow + CI + branch protection
- [docs/constraints.md](docs/constraints.md) — what NOT to do
- [docs/retrospectives/](docs/retrospectives/) — retrospectives (see Self-improvement log)

## Current state

MVP scoped (PRD/PLAN), stack via ADRs 002–004 (FastAPI `api/` on Vercel, Postgres, OpenRouter).
**Frontend (features 002–007 012 016 017 019):** render-only board, tag-click filtering,
takeaway deep links, per-card UA|RU|EN translate switcher, and a per-card "Похожие" button
(feature 019: `findSimilar` → `resolveSimilar` → inline list; click scrolls + highlights the
target card; bundled `SimilarUiProps`). Real-API `lib/api.ts` (Vite proxy in dev; vitest keeps
the mock). 103 vitest green.
**Backend (features 004 008–011 014 015 019 020):** `POST /api/digest {url, language}` — ELI5
digest: simple-words explanation, `keyPoints = [{takeaway, quote|null}]` (quotes verified
code-side), canonical lowercase tags, language uk/ru/en; category resolved against stored
sections before save (feature 020: `categories.py` port of feature 002 + `list_categories`).
`POST /api/cards/{id}/translate {language}` re-extracts + re-digests in place (category
resolved the same way). `POST /api/cards/{id}/similar` ranks other board cards by meaning
(`similar.py`, one OpenRouter call, ids filtered to the board). Plus GET/DELETE cards,
Postgres. 146 pytest green.
**Deployed (feature 013, issue #11): https://content-digest.vercel.app** — public (owner's
choice), Neon Postgres via Vercel integration (env vars are sensitive: values exist only inside
deployments), OpenRouter funded → paid default model. Prod e2e green: digest → persist → list →
delete. Deploys via `npx vercel deploy --prod` (GitHub auto-deploy not wired yet).
**Backlog:** rate limiting, GitHub auto-deploy, shared `makeCard` spec factory (three fixture
fan-outs in a row — retros 016/017).

## Dev server

From the repo root: `npm run dev` → `http://127.0.0.1:5174/` (port read from `.dev-port`,
defaults 5174).

## Common commands

Frontend (from repo root):

- `npm run dev` — start the dev server
- `npm run build` — type-check + production build
- `npm run preview` — preview the built app
- `npm run test` / `npm run test:run` — Vitest (watch / single run)
- `npm run lint` — ESLint
- `npm run format` — Prettier

Backend (from `api/`; Python 3.10+, 3.12 recommended — Vercel runtime is 3.12; see
[api/README.md](api/README.md)):

- `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt` — one-time setup
- `uvicorn index:app --host 127.0.0.1 --port 8000` — run the API locally (venv active)
- `python -m pytest` — backend tests (venv active)
- `curl http://127.0.0.1:8000/api/health` — health check → `{"status":"ok"}`

## Critical files

- [app/vite.config.ts](app/vite.config.ts) — dev/preview ports + `@/*` path alias (single
  source of truth)
- [app/vitest.config.ts](app/vitest.config.ts) — test runner config
- [docs/constraints.md](docs/constraints.md) — guardrails

## Self-improvement log

- [001-hello-world](docs/retrospectives/001-hello-world.md) — bootstrap retro; added the
  "vite.config.ts is source of truth for ports" constraint.
- [002-category-normalization](docs/retrospectives/002-category-normalization.md) — pure
  module ahead of its save-path dependency; flagged the pre-existing TS 6 `baseUrl` build
  failure.
- [003-card-model](docs/retrospectives/003-card-model.md) — board data layer; issue text
  misnamed the feature-002 export (`resolveCategory`).
- [004-api-scaffold](docs/retrospectives/004-api-scaffold.md) — FastAPI skeleton; system
  python3 was 3.9, installed Homebrew python@3.12 to match the Vercel runtime.
- [005-board-ui](docs/retrospectives/005-board-ui.md) — render-only components; reused
  bootstrap CSS variables for dark mode.
- [006-url-input](docs/retrospectives/006-url-input.md) — `toErrorMessage` extracted so the
  component stays render-only.
- [007-api-client](docs/retrospectives/007-api-client.md) — `erasableSyntaxOnly` forbids TS
  parameter properties; vitest doesn't catch what `tsc -b` does, so run the full trio.
- [008-extract](docs/retrospectives/008-extract.md) — trafilatura; `MIN_TEXT_CHARS` guard
  enforces "never a blank card".
- [009-digest](docs/retrospectives/009-digest.md) — client-injection seam for httpx tests;
  snake_case `key_points` ↔ camelCase mapping deferred to the route layer (#8).
- [010-digest-route](docs/retrospectives/010-digest-route.md) — smoke test caught two bugs unit
  tests can't (UA 403, free-tier 402); browser UA now part of fetch_html's contract.
- [011-cards-persistence](docs/retrospectives/011-cards-persistence.md) — storage layer done,
  live DB check deferred: the Vercel account had no Postgres despite expectations — verify
  external resources exist via API before planning around them.
- [012-frontend-real-api](docs/retrospectives/012-frontend-real-api.md) — Backend-seam swap
  needed zero component changes; a fetch Response body is single-use in specs.
- [013-vercel-deploy](docs/retrospectives/013-vercel-deploy.md) — sensitive env vars are
  unreadable outside deployments (ensure-schema on cold start); Vercel python needs a sys.path
  shim; static-build mounts under the source-dir prefix.
- [014-eli5-digest](docs/retrospectives/014-eli5-digest.md) — verify model quotes against the
  full source, not the truncated prompt; normalize sloppy model output instead of rejecting.
- [016-tag-filtering](docs/retrospectives/016-tag-filtering.md) — KeyPoint shape coordinated
  with the parallel backend agent via the type alone.
- [015-translate-card](docs/retrospectives/015-translate-card.md) — `_COLUMNS` is the single
  source of row-tuple order: change it, both mappers, and the roundtrip fixture together.
- [017-card-translate-ui](docs/retrospectives/017-card-translate-ui.md) — disabled-button-as-
  no-op keeps components render-only; extract a shared makeCard spec factory next touch.
- [018-live-bugfixes](docs/retrospectives/018-live-bugfixes.md) — OpenRouter routed Vercel
  egress to a 20×-slower provider (fix: provider sort=latency + haiku-4.5 → 177s→9s); dashes
  and bullet markers silently broke text-fragment links.
- [019-similar-materials](docs/retrospectives/019-similar-materials.md) — bundled per-card props
  into one object to keep components render-only; a shared `openrouter.py` helper is the next
  step now that two callers duplicate the call skeleton.
- [020-category-normalization-on-save](docs/retrospectives/020-category-normalization-on-save.md)
  — issue #12's "remaining work" note went stale when the save path moved server-side; ported
  the module with a mirrored spec as the TS↔Python sync mechanism.

## Escalation rules

Stop and ask via AskUserQuestion when:

- The same test has failed 3 times with different fixes (you're guessing — get more context).
- A request conflicts with `docs/constraints.md` or a rule in the "Rules" section of
  `CLAUDE.md` (surface it, don't silently comply).
- A new runtime dependency is needed (ask + add an ADR before installing).
- `:5174` or `:4173` is taken (fix the conflict, do not let Vite drift to another port).
- This change would push `CLAUDE.md` past ~200 lines (route detail into a linked doc first).
- Acceptance criteria in a `docs/requirements/feature-*.md` are ambiguous or contradict each
  other.

## Rules

**TypeScript strict:** Do NOT disable `strict`, `noImplicitAny`, `strictNullChecks`, or
`noUncheckedIndexedAccess` in any `tsconfig*.json`. Narrow the type or guard the value — never
loosen the config.

**Pure modules:** Business logic lives in pure modules under `app/src/`. React components only
render — no branching/transform logic. Extract any non-trivial computation into a pure module
and spec it before wiring it in.

**Spec first:** Every new module starts with a failing `*.spec.ts(x)` test. Show the red
output, then write the minimum code to turn it green, then commit.
