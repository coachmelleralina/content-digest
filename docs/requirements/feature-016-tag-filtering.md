# Feature 016 — Tag filtering + takeaway deep links (issue #15)

## User stories

- As a reader, I want tags to be clickable, so that clicking a tag shows me every article on
  that topic (PRD: "canonical reusable topics").
- As a reader, I want each takeaway to be clickable and lead to the exact passage in the
  original article, so that I can read the source of that thought in context (PRD: text-fragment
  deep link with the grounding quote).

## Data model change (coordinated with backend issue #13)

`Card.keyPoints` migrates from `string[]` to `KeyPoint[]`:

```ts
type KeyPoint = { takeaway: string; quote: string | null };
```

`takeaway` is the simple-language thought; `quote` is the verbatim grounding passage from the
article (or `null` when the model could not ground the point). The backend (issue #13, built in
parallel) emits the same shape; the frontend coordinates via this type only. Mocks and spec
fixtures migrate in this feature; the mock card generator in `lib/api.ts` gets a minimal
compile-fix (`quote: null`) with no signature changes.

## Acceptance criteria

**Pure modules (spec-first):**

- `filterByTag(cards, tag)` (`lib/filterByTag.ts`):
  - GIVEN `tag === null` THEN all cards are returned.
  - GIVEN a tag, THEN only cards whose `tags` contain it are returned, matched
    case-insensitively (`'AI'` matches `'ai'`).
  - GIVEN a tag no card has, THEN `[]`.
  - `isSameTag(a, b)` — the same case-insensitive equality, exposed so components can mark the
    active chip without embedding comparison logic.
- `takeawayHref(articleUrl, quote)` (`lib/fragmentUrl.ts`):
  - GIVEN `quote === null` THEN `null` (takeaway renders as plain text).
  - GIVEN a quote, THEN `${urlWithoutFragment}#:~:text=${encodeURIComponent(quote)}`.
  - GIVEN an article URL that already has a `#fragment`, THEN the existing fragment is stripped
    before the text fragment is appended.
  - Spaces, quotes, and Cyrillic in the quote are percent-encoded.

**UI:**

- Tag chips on cards are buttons (pointer cursor, real `<button>` semantics) calling
  `onTagClick(tag)`; the active tag is visually distinct.
- GIVEN an active tag, WHEN the board renders, THEN it shows `filterByTag(cards, activeTag)`;
  filtering logic lives in App via the pure module — `Board`/`Section`/`Card` stay render-only
  (pass-through props `onTagClick`, `activeTag`).
- WHEN the user clicks the already-active tag, THEN the filter clears.
- An active-filter bar between `UrlInput` and `Board` shows «Показано: #тег ✕»; clicking ✕
  clears the filter.
- GIVEN an active tag that matches zero cards, THEN App shows a «ничего с этим тегом» state
  instead of the board's "paste a link" empty state (which remains for a truly empty board).
- Takeaways with a quote render as links (`target="_blank" rel="noopener noreferrer"`, visibly
  link-styled) via `takeawayHref`; takeaways without a quote render as plain text.
- Card title still opens the original article (verify only — no change).

## Out of scope

- Backend `key_points` emission with quotes — issue #13.
- Per-card translation UI — issue #16 (shares `Card.tsx`/`App.tsx`, rebases on this branch).
- Persisting the active filter (URL/query param or storage) — filter is session state.
- Multi-tag (AND/OR) filtering.
