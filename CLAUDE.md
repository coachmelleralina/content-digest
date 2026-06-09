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
   `.dev-port` (defaults to 5173, probed for a free port at bootstrap time). Always read the
   current port from `.dev-port` instead of hardcoding 5173. `strictPort: true` is set so Vite
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
- [docs/requirements/feature-001-hello-world.md](docs/requirements/feature-001-hello-world.md) — Feature 001
- [docs/decisions/001-agent-structure.md](docs/decisions/001-agent-structure.md) — ADR: root-vs-`app/` split
- [docs/constraints.md](docs/constraints.md) — what NOT to do
- [docs/retrospectives/](docs/retrospectives/) — retrospectives (see Self-improvement log)

## Current state

Hello world greeting rendered; no features specced beyond Feature 001.

## Dev server

From the repo root: `npm run dev` → `http://127.0.0.1:5173/` (port read from `.dev-port`,
defaults 5173).

## Common commands (all from repo root)

- `npm run dev` — start the dev server
- `npm run build` — type-check + production build
- `npm run preview` — preview the built app
- `npm run test` / `npm run test:run` — Vitest (watch / single run)
- `npm run lint` — ESLint
- `npm run format` — Prettier

## Critical files

- [app/vite.config.ts](app/vite.config.ts) — dev/preview ports + `@/*` path alias (single
  source of truth)
- [app/vitest.config.ts](app/vitest.config.ts) — test runner config
- [docs/constraints.md](docs/constraints.md) — guardrails

## Self-improvement log

- (none yet — populated after each feature retro)

## Escalation rules

Stop and ask via AskUserQuestion when:

- The same test has failed 3 times with different fixes (you're guessing — get more context).
- A request conflicts with `docs/constraints.md` or a rule in the "Rules" section of
  `CLAUDE.md` (surface it, don't silently comply).
- A new runtime dependency is needed (ask + add an ADR before installing).
- `:5173` or `:4173` is taken (fix the conflict, do not let Vite drift to another port).
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
