# ADR 004 — OpenRouter for the AI digest

## Status

Accepted.

## Context

The digest step turns extracted article text into a summary, key points, tags, and a category.
We need one AI provider and a model choice. The user chose a **mid-tier "balanced" model**
(good quality at reasonable cost) and **AI-chosen category labels** (the model names the topic
itself rather than picking from a fixed list).

## Decision

- Call the AI via **OpenRouter** (one HTTP endpoint, easy to swap models). A single
  chat-completion call returns `{ summary, keyPoints[], tags[], category }` as structured JSON.
- Use a **mid-tier balanced model**. The exact model id is a config value (env var / one
  constant in `api/digest.py`) so it can be changed in one place without code churn. Pick the
  concrete model when implementing the digest feature.
- **Categories are free-form, AI-chosen** — the model proposes the topic label; the board
  creates sections dynamically from whatever categories appear.
- The `OPENROUTER_API_KEY` is server-side only (backend), never exposed to the client.

## Consequences

- Adds `OPENROUTER_API_KEY` to `.env.example` and Vercel env vars.
- Free-form categories mean near-duplicate labels are possible (e.g. "AI" vs "Artificial
  Intelligence"). Accepted for the MVP; a later normalization/merge pass is a P1/P2 item — track
  in the PRD.
- Model choice is reversible: swapping the model id is a one-line change, so we can tune the
  cost/quality balance after seeing real output.
- The digest logic (`api/digest.py`) stays a pure-ish module taking text and returning the
  structured result, so it can be unit-tested against fixed inputs.
