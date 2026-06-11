-- Feature 011 (issue #9) — cards table, per ADR 003 / docs/PLAN.md.
-- Idempotent: safe to run more than once.

CREATE TABLE IF NOT EXISTS cards (
    id          uuid        PRIMARY KEY,
    url         text        NOT NULL,
    title       text        NOT NULL,
    summary     text        NOT NULL,
    key_points  jsonb       NOT NULL,
    tags        jsonb       NOT NULL,
    category    text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS cards_created_at_idx ON cards (created_at DESC);

-- Feature 015 (issue #14) — digest language per card; existing rows backfill to 'uk'.
ALTER TABLE cards ADD COLUMN IF NOT EXISTS language text NOT NULL DEFAULT 'uk';
