# Retrospective 013 — Vercel deployment (issue #11)

## What we did

Deployed the MVP to production: explicit `vercel.json` builds (only `api/index.py` becomes a
function; Vite static build from `app/`), `.vercelignore` for tests/fixtures/venv, ensure-schema
on cold start, `OPENROUTER_API_KEY` added to Vercel env (account funded → default
`anthropic/claude-3.5-haiku` per ADR 004; local free-model override removed). Production e2e
passed end to end at **https://content-digest.vercel.app**: health → real digest (card persisted
in Neon) → list → delete 204 → 404 on re-delete.

## What worked

- The deploy revealed issues in minutes that no local test could: each fix was one commit.
- Ensure-schema-on-cold-start removed the manual migration step entirely — necessary because
  Neon-integration env vars are **sensitive** (values unreadable outside deployments; even
  `vercel env pull` returns empty strings).
- Error mapping kept its promise at every failure: SSO 401, import crash, fetch 403/402/429 —
  the user-facing body was always clean.

## What didn't / friction points

- **`vercel env pull` silently returns EMPTY values for sensitive vars** — looked like a bug,
  was by design. Cost three debugging rounds. Lesson recorded: integration secrets live only
  inside deployments; local dev needs the connection string copied from the Neon dashboard.
- **Vercel python doesn't put the entrypoint's directory on sys.path** → `ModuleNotFoundError:
  No module named 'db'`. Fixed with a `sys.path.insert` shim in index.py (no-op locally).
- **@vercel/static-build mounts output under the source dir prefix** (`/app/...`), not at the
  root → initial 404; routes now map `/assets/*` and `/` to the `/app/` prefix explicitly.
- **Deployment Protection (Vercel Authentication) is on by default for team projects** → 401
  for everyone but the owner. Disabled for production with the user's explicit approval (the
  harness classifier correctly blocked the unauthorized first attempt).
- GitHub auto-deploy connect failed during `vercel link`; deploys are via CLI for now.

## Decisions to carry forward

- Production model is the paid ADR-004 default; if free-tier limits are ever wanted again, set
  `OPENROUTER_MODEL` in Vercel env, not in code.
- Public access is a product decision recorded here: the user chose public; anyone with the URL
  can add cards and spends the OpenRouter balance. Rate limiting is a candidate next feature.

## Changes made to CLAUDE.md / constraints / working agreement

- CLAUDE.md TOC/state/log updated; deployment section added to Current state. No
  working-agreement changes.

## Open questions for next session

- Wire GitHub→Vercel auto-deploy (failed connect during link).
- Local backend dev against the prod DB needs the Neon connection string copied manually from
  the dashboard (optional; prod e2e covers verification for now).
- Consider basic abuse protection (rate limit per IP) now that the app is public.
