# Feature 013 — Vercel deployment (issue #11)

## User story

As the product owner, I want the app deployed on Vercel with the hosted Neon Postgres and the
real AI provider, so that the full paste → digest → board loop works at a public URL, not just
on localhost.

## Acceptance criteria

- GIVEN the deployed URL
  WHEN the browser loads it
  THEN the Vite-built frontend is served, and `/api/health` answers `{"status":"ok"}` on the
  same origin.
- GIVEN a real article URL posted to `/api/digest` on the deployed origin
  THEN a real AI digest card is returned AND persisted in Neon (visible via `GET /api/cards`),
  and `DELETE /api/cards/{id}` removes it — closing the live-verification gates of issues #9
  and #10.
- Env: `DATABASE_URL` (Neon integration, sensitive — injected by Vercel) and
  `OPENROUTER_API_KEY` (added as a Vercel env var; account now has credits → default
  `anthropic/claude-3.5-haiku` per ADR 004).
- The schema self-initializes: `schema.sql` is idempotent and runs on backend cold start when
  `DATABASE_URL` is present (sensitive vars are unreadable outside deployments, so a manual
  migration step is impossible without copying secrets around — recorded decision).
- Only `api/index.py` is exposed as a serverless function (explicit `builds`); tests, fixtures
  and venv are excluded via `.vercelignore`.

## Out of scope

- Custom domain, analytics, CI gate (Deferred list in boilerplate).
- GitHub→Vercel auto-deploy wiring (the `vercel link` GitHub connect failed; CLI deploys work —
  revisit later).

## Verification

`curl` against the production URL: health 200 → digest 200 with real card → cards list contains
it → delete 204 → list empty again. Then a browser check of the same flow.
