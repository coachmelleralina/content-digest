# PRD — Content Digest

## Problem Statement

People who read a lot online save more articles than they can read, and saved links become an
unstructured backlog with no summary and no organization. Re-opening each link to remember what
it was about is slow, so most saved articles are never revisited. Content Digest turns a pasted
link into a structured, skimmable card and files it on a topic-organized board.

**Who:** a single reader (researcher, knowledge worker, student, the curious) running the app
client-side in the browser. No accounts, no team features.

## Goals

1. Reduce "what was this article about?" from re-reading the whole piece to scanning one card
   (summary + key points visible without opening the source).
2. Keep a growing reading list navigable by auto-grouping cards into topic sections, with zero
   manual filing.
3. Make capture effortless: paste a URL → a complete card with no further input required.
4. Earn trust: never produce a blank or broken card — bad URLs and failed extraction fail
   visibly and recoverably.

## Non-Goals

1. **No accounts / multi-user / shared boards** — solo, local MVP; auth is a separate
   initiative.
2. **No hosted backend or database** beyond what extraction/AI calls strictly require — keeps
   the MVP shippable client-side.
3. **No capture surfaces beyond paste** (browser extension, mobile, RSS, bulk import,
   scheduled fetch) — validate the core loop first.
4. **No reading/annotation layer** (full-text storage, reader mode, highlights) — Content
   Digest summarizes, it isn't a reader.
5. **No search / advanced filtering / custom taxonomies** in v1 — topic sections are the only
   organizing primitive for now.

## User Stories

**Reader — capture**
- As a reader, I want to paste an article URL and get a card automatically, so that saving an
  article takes one action and no typing.
- As a reader, when a URL is unreachable or can't be parsed, I want a clear error instead of a
  broken card, so that I trust what lands on my board.

**Reader — digest**
- As a reader, I want each card to show a short summary and key points, so that I can recall an
  article without re-opening it.
- As a reader, I want tags and a suggested category on each card, so that related articles are
  findable and grouped.

**Reader — organize & manage**
- As a reader, I want new cards filed into a section matching their category, so that my board
  stays organized without manual sorting.
- As a reader, I want to open the original link, move a card to another section, and delete a
  card, so that I stay in control of the board.
- As a reader, I want my cards to still be there after a page reload, so that the board is a
  durable reading list, not a scratchpad.

## Requirements

### Must-Have (P0)

- **URL capture flow.** Input + submit with explicit loading and error states.
  - Given a pasted URL, when I submit, then I see a loading state and then either a card or a
    clear error.
  - Given an unreachable/unparseable URL, when extraction fails, then I see a specific error
    and no card is created.
- **Article extraction.** Pull the readable article body from the URL.
  - Given a typical article URL, when processed, then the main text is extracted (nav/ads/boilerplate excluded well enough to summarize).
- **AI digest.** From the extracted text, produce a short summary, key points, and tags.
  - Given extracted text, when the digest runs, then the card shows a summary, ≥1 key point,
    and ≥1 tag.
- **Suggested category.** Assign exactly one topic category per article.
  - Given a processed article, then it has exactly one category used for board placement.
- **Board with topic sections.** Cards render as cards; cards group into sections by category.
  - Given two articles with the same category, when both are saved, then they appear in the
    same section.
- **Card management.** Read card, open source link, move card between sections, delete card.
- **Local persistence.** Cards survive a full page reload (browser-local storage).
  - Given saved cards, when I reload, then the same cards and sections are present.
- **Pure, testable pipeline.** Extraction, summarization, tagging, categorization are pure
  modules; the UI only renders their output (per `docs/constraints.md`).

### Nice-to-Have (P1)

- Manual edit of a card's tags or category (override the AI).
- Empty-state and first-run guidance on the board.
- Re-run digest on an existing card.

### Future Considerations (P2)

- Search and filtering across cards.
- Accounts + sync so boards persist across devices.
- Additional capture surfaces (extension, share target).
- Custom/renamable category taxonomy.

## Success Metrics

*Solo MVP — measured by observation/manual checks, not analytics tooling yet. Targets are
hypotheses to validate.*

**Leading (per session):**
- Capture success rate: ≥90% of valid article URLs produce a complete card (summary + ≥1 key
  point + ≥1 tag + category).
- Graceful-failure rate: 100% of failed extractions show an error and create no broken card.
- Time to card: a single article digests in a "reasonable" wait (target < ~15s) without
  blocking the UI.

**Lagging (over weeks of use):**
- Revisit value: the user can identify an article from its card alone (without opening the
  source) in the large majority of cases — the core "do I still need to read this?" job.
- Retention of the habit: the board accumulates and is still consulted, rather than abandoned.

## Open Questions

Resolved (see ADRs):
- ~~Extraction approach~~ → server-side in the FastAPI `api/` service ([ADR 002](decisions/002-backend-api-on-vercel.md)).
- ~~AI provider/model + key handling~~ → OpenRouter, mid-tier balanced model, key server-side only ([ADR 004](decisions/004-openrouter-ai.md)).
- ~~Category set~~ → free-form, **AI-chosen** labels; sections created dynamically ([ADR 004](decisions/004-openrouter-ai.md)).
- ~~Persistence~~ → **Postgres from the start**, not localStorage ([ADR 003](decisions/003-postgres-storage.md)).

Still open:
- **[product — non-blocking]** Near-duplicate AI category labels (e.g. "AI" vs "Artificial
  Intelligence") — accepted for MVP; add a normalization/merge pass as a P1/P2 follow-up.
- **[engineering — non-blocking]** Which Postgres provider (Vercel Postgres vs Neon) — decided
  at deploy time; no code impact.

## Timeline Considerations

- No external/contractual deadlines (personal project).
- **Dependency:** the two blocking engineering questions (extraction + AI provider) gate the
  first real feature; each needs an ADR before implementation, per the repo working agreement.
- **Suggested phasing:** (1) capture + extraction + digest producing one card; (2) board with
  topic sections + persistence; (3) card management (move/delete/open). Each phase ships
  spec-first with its own `docs/requirements/feature-*.md` and retro.
