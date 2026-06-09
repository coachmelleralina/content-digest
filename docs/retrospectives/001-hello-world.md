# Retrospective 001 — Hello World Bootstrap

## What we did

Scaffolded a Vite + React + TypeScript app into `app/`, set up root pass-through scripts and
dotfiles (`.gitignore`, `.editorconfig`, `.nvmrc`, `.env.example`), wrote the agentic-engineering
governance layer at the repo root (`CLAUDE.md`, `README.md`, `docs/requirements`, `docs/decisions`,
`docs/constraints.md`, `docs/retrospectives`), and shipped hello world spec-first as Feature 001
(requirements doc → failing `greeting.spec.ts` → minimal `greeting.ts` → green → `App.tsx` rewired
to render it). Probed a free dev port, brought the dev server up, and confirmed HTTP 200 with the
React mount point present.

## What worked

- Spec-first loop ran cleanly: red (`Cannot find module './greeting'`) → impl → green (1 passed),
  exactly the discipline the working agreement asks for.
- The root-vs-`app/` split kept governance and app code cleanly separated; pass-through scripts
  mean every command runs from the repo root without `cd app`.
- Port probing caught a real conflict (`:5173` already in use) and selected `:5174` deterministically
  instead of letting Vite silently drift.
- Lint passed clean on the first run; ESLint 10 flat config restricts to `**/*.{ts,tsx}` via the
  `files` glob, so no extra wiring was needed.

## What didn't / friction points

- **Scaffold tsconfig had no `strict`.** The current Vite `react-ts` template's `tsconfig.app.json`
  does NOT set `"strict": true` — the boilerplate's "confirm, don't assume" warning was right. Added
  `strict` + `noImplicitAny` + `strictNullChecks` + `noUncheckedIndexedAccess` explicitly.
- **Port sed didn't cover `vite.config.ts`.** Step 6.1's sed rewrites only `CLAUDE.md` and
  `README.md`. Because `:5173` was taken, `vite.config.ts` still pinned `port: 5173` with
  `strictPort: true`, which would have failed to bind — had to update it by hand to `5174`. Future
  bootstraps on a busy machine should expect this manual step.
- **`eslint . --ext ts,tsx` is stale for ESLint 10.** The boilerplate's suggested lint script uses
  the `--ext` flag, which the flat-config CLI no longer honors. Kept the scaffold's `eslint .`
  (file scoping lives in the flat config) — same class of incompatibility the boilerplate already
  flags for `eslint-plugin-react`.

## Decisions to carry forward

- No new ADR needed beyond [001-agent-structure](../decisions/001-agent-structure.md); the layout
  decision covers this session.

## Changes made to CLAUDE.md / constraints / working agreement

- Added a constraints note that `app/vite.config.ts` is the single source of truth for dev/preview
  ports and must be kept in sync with `.dev-port` / `.preview-port` after a port probe.
- No working-agreement rule changes — the workflow held up.

## Open questions for next session

- When the extraction feature is specced: does it run purely client-side (fetch + a readability
  parser) or via a small proxy to avoid CORS? Needs an ADR.
- Which AI provider powers summarization/tagging, and how is its key supplied via `.env`? Needs an
  ADR + `.env.example` entry.
