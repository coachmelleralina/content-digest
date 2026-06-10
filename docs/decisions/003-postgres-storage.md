# ADR 003 — Postgres for storage (from the start)

## Status

Accepted.

## Context

Cards must persist across reloads and (eventually) across devices. The PRD originally assumed
browser-local storage for v1. The user chose to use a hosted database from the start rather
than starting local and migrating later.

## Decision

- Use **Postgres** as the single store, provisioned through **Vercel** (Vercel Postgres / Neon)
  to match the Vercel-based deployment ([ADR 002](002-backend-api-on-vercel.md)). Exact provider
  picked at deploy time; it does not affect application code (standard `DATABASE_URL`).
- One `cards` table: `id`, `url`, `title`, `summary`, `key_points` (jsonb), `tags` (jsonb),
  `category`, `created_at`. Schema lives in `api/schema.sql`.
- All DB access goes through the backend (`api/db.py`); the frontend never holds a DB
  connection string.

## Consequences

- Supersedes the "no database" bootstrap constraint and the PRD's localStorage assumption for
  the MVP. The board loads from `GET /api/cards`.
- A `DATABASE_URL` is required to run the backend; add it to `.env.example` and Vercel env vars.
- Connecting to Postgres from short-lived serverless functions needs pooling-friendly access
  (the chosen provider's pooled connection string) — note this when implementing `db.py`.
