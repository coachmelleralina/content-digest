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
12. **CLAUDE.md ≤ ~200 lines.** It is a router, not an encyclopedia. If a retro update would
    push it past ~200 lines, move detail into a linked file under `docs/` and link from here
    instead. Same applies to `constraints.md` — split into topical files once over ~150 lines.

## Documentation TOC

- [docs/requirements/overview.md](docs/requirements/overview.md) — goal, user, success criteria
- [docs/PRD.md](docs/PRD.md) — product requirements (problem, scope, MVP success criteria)
- [docs/PLAN.md](docs/PLAN.md) — MVP build plan (stack, folder structure, build steps)
- [docs/requirements/feature-001-hello-world.md](docs/requirements/feature-001-hello-world.md) — Feature 001
- [docs/requirements/feature-002-category-normalization.md](docs/requirements/feature-002-category-normalization.md) — Feature 002 (issue #12)
- [docs/requirements/feature-003-card-model.md](docs/requirements/feature-003-card-model.md) — Feature 003 (issue #1)
- [docs/requirements/feature-004-api-scaffold.md](docs/requirements/feature-004-api-scaffold.md) — Feature 004 (issue #5)
- [docs/requirements/feature-005-board-ui.md](docs/requirements/feature-005-board-ui.md) — Feature 005 (issue #2)
- [docs/requirements/feature-006-url-input.md](docs/requirements/feature-006-url-input.md) — Feature 006 (issue #3)
- [docs/requirements/feature-007-api-client.md](docs/requirements/feature-007-api-client.md) — Feature 007 (issue #4)
- [docs/requirements/feature-008-extract.md](docs/requirements/feature-008-extract.md) — Feature 008 (issue #6)
- [docs/requirements/feature-009-digest.md](docs/requirements/feature-009-digest.md) — Feature 009 (issue #7)
- [docs/decisions/001-agent-structure.md](docs/decisions/001-agent-structure.md) — ADR: root-vs-`app/` split
- [docs/decisions/002-backend-api-on-vercel.md](docs/decisions/002-backend-api-on-vercel.md) — ADR: `api/` backend on Vercel
- [docs/decisions/003-postgres-storage.md](docs/decisions/003-postgres-storage.md) — ADR: Postgres storage
- [docs/decisions/004-openrouter-ai.md](docs/decisions/004-openrouter-ai.md) — ADR: OpenRouter AI digest
- [docs/constraints.md](docs/constraints.md) — what NOT to do
- [docs/retrospectives/](docs/retrospectives/) — retrospectives (see Self-improvement log)

## Current state

MVP scoped (PRD/PLAN), stack via ADRs 002–004 (FastAPI `api/` on Vercel, Postgres, OpenRouter).
**Frontend (features 002–007, issues #12 #1 #2 #3 #4):** board UI renders cards grouped by
category (`Board`/`Section`/`Card`, render-only), `UrlInput` + `validateUrl`, mock-backed
`lib/api.ts` (`digestUrl`/`listCards`/`deleteCard` + `ApiError`) wired into `App.tsx` —
end-to-end mock flow works in the browser. 64 vitest tests green.
**Backend (features 004 008 009, issues #5 #6 #7):** FastAPI scaffold + `extract.py`
(trafilatura, typed errors) + `digest.py` (OpenRouter, default `anthropic/claude-3.5-haiku`,
strict JSON parsing). 29 pytest tests green. Not yet routed — `POST /api/digest` is issue #8.
**Next:** #8 (route) → #9 (Postgres) → #10 (swap mock backend for fetch) → #11 (deploy).

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
- [003-card-model](docs/retrospectives/003-card-model.md) — data layer for the board;
  issue text said `normalizeCategory` but the real export is `resolveCategory`.
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
