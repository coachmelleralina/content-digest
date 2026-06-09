# ADR 001 — Agent structure: root-vs-`app/` split

## Status

Accepted (bootstrap).

## Context

This project follows agentic engineering, not vibe coding: specs precede code, decisions are
recorded, constraints are explicit, and the workflow improves via retrospectives. For that to
hold, the **governance layer** (instructions for the agent, requirements, decisions, retros,
constraints) must not get tangled up with **application code**. If `CLAUDE.md` and `docs/`
lived inside the Vite app, they would be subject to the app's build tooling, linting, and
refactors, and the boundary between "how we work" and "what we built" would blur.

## Decision

Physically separate the two layers in the directory tree:

- The **repo root** holds governance and project-level config only: `CLAUDE.md`, `README.md`,
  `docs/**`, root `package.json` (pass-through scripts via `npm --prefix app`), and dotfiles
  (`.gitignore`, `.editorconfig`, `.nvmrc`, `.env.example`).
- **All** Vite + React + TypeScript application code lives under `app/`. The app has its own
  `package.json`, `vite.config.ts`, `vitest.config.ts`, and dependencies.
- `docs/` is subdivided by intent:
  - `requirements/` — the goal overview and one file per feature.
  - `decisions/` — ADRs like this one, for any architectural choice.
  - `retrospectives/` — one retro per feature, feeding workflow improvements back into
    `CLAUDE.md`.
  - `constraints.md` — the running "what NOT to do" list.

Git is initialized at the repo root so both layers are versioned together as one project.

## Consequences

- A single source of truth for "how Claude works here" (`CLAUDE.md`) sits at the root and is
  never reachable by the app's tooling.
- Commands run from the repo root via pass-through scripts, so contributors never need to
  `cd app` for everyday tasks.
- The split must be actively maintained: no governance files inside `app/`, no app code at the
  root. This is enforced as a constraint and a working-agreement rule.
- Introducing a second package later (e.g. `packages/shared/`) would justify revisiting the
  pass-through scripts in favor of npm workspaces — a future ADR.
