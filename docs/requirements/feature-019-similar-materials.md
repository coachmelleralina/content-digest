# Feature 019 — Similar materials (find related cards on the board)

## User story

As a reader, I want a "Похожие" button on a card that shows my OTHER saved cards on the same
topic, so that I can jump back to related reading I already collected.

## Acceptance criteria

- GIVEN a card and at least one other card on the board
  WHEN I click "Похожие" on that card
  THEN I see up to 3 of my other cards judged most related BY MEANING (AI), each with a one-line
  "why related" reason in the card's language.
- GIVEN I click a result
  THEN the board scrolls to that card and briefly highlights it.
- GIVEN the board has only this one card
  THEN the "Похожие" button is disabled ("пока не с чем сравнивать") and no AI call is made.
- GIVEN no related cards are found
  THEN I see "На доске пока нет похожих материалов".
- GIVEN extraction/AI/DB failure
  THEN a clean `{detail}` error surfaces (no blank/broken state) — same mapping as other routes.
- The AI ranks ONLY cards already on the board (no web search) — chosen scope (Variant A).

## API contract (backend)

`POST /api/cards/{id}/similar` → `200 [{ "id": "<other card id>", "reason": "<one sentence>" }]`
(0–3 items, most related first, only ids that exist on the board). 404 for unknown id;
500 (config/DB) / 502 (AI) on failure. The reason language follows the target card's `language`.

## Design (Variant A — AI ranks the board)

- `api/similar.py`: one OpenRouter call. Input = target card (title/summary/tags) + the other
  cards (id/title/summary/tags). Output = strict JSON `{"similar":[{"id","reason"}]}`; code
  filters returned ids to the real candidate set, dedupes, caps at 3. Empty board of others →
  returns `[]` WITHOUT calling the AI.
- Frontend: `lib/resolveSimilar.ts` (pure) maps refs → `{id, title, reason}` against the current
  cards (drops ids not on the board). `Card` gets a "Похожие" button + an inline results list;
  clicking a result scrolls to + highlights the target card. State (results per card, which card
  is loading, which is highlighted) lives in `App`; components stay render-only.

## Out of scope

- Web search for NEW external articles (a future "найти ещё в вебе" button — Variant B/hybrid).
- Embeddings / pgvector similarity (Variant B) — kept as P2 architectural insurance; swapping
  `similar.py` for an embeddings backend later is a local change.
- Re-ranking on every board change / caching results.

## Open questions

- None blocking. Result count capped at 3 for the MVP; revisit if boards grow large (then
  Variant B / pagination).
