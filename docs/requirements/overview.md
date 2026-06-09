# Overview

## Goal

content-digest turns a raw article link into a structured, skimmable card. You paste a URL; the
app extracts the article text, an AI step produces a short summary, a list of key points, and a
set of tags, and suggests a category for the piece. Each result is saved as a card on a board
whose sections are organized by topic, so a growing reading list stays navigable at a glance.

## Primary user / context

Anyone who reads a lot online and wants an at-a-glance digest of articles instead of re-reading
them — researchers, knowledge workers, the curious. It runs entirely client-side in the
browser via the local dev server during development.

## Success criteria

- A user can paste an article URL and, after processing, see a card containing: a short
  summary, key points, tags, and a suggested category.
- Cards are grouped into topic sections on a board and remain there across the session.
- The pipeline pieces (text extraction, summarization, tagging, categorization) are pure,
  independently testable modules with the UI only rendering their output.
- The app builds, lints clean, and every feature ships with a passing spec.

## Out of scope (for the bootstrap and near term)

- No authentication, user accounts, or multi-user state.
- No backend or database in the bootstrap. Article extraction and AI summarization are
  **deferred features**, each gated behind its own `docs/requirements/feature-*.md` and its own
  preflight (e.g. an API key or extraction service) before any runtime dependency is added.
- No client-side routing / multi-page navigation for now.

## Notes / future questions

- Where does extraction run (client fetch + readability, or a small server/proxy to dodge
  CORS)? Decide via an ADR when the extraction feature is specced.
- Which AI provider powers summarization/tagging, and how is the key supplied? Decide via an
  ADR + `.env.example` entry when that feature is specced.
