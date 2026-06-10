# Feature 005 — Board UI: Board / Section / Card components (render-only)

Tracks GitHub issue [#2](https://github.com/coachmelleralina/content-digest/issues/2).
Second slice of PLAN build step 1 ("Frontend shell, no AI yet"): render-only React
components that display the feature-003 data layer (`mockCards` grouped by
`groupByCategory`) as a topic board.

## User story

As the board's only user, I want my saved article cards rendered as a readable board —
topic sections with headed groups of cards, each card showing title, summary, key points,
tags, and category — so I can scan my recent reading by topic in the browser instead of
in a fixtures file.

## Scope

1. **`app/src/components/Card.tsx`** — renders one `Card`:
   - title as a link to `card.url`, opening in a new tab (`target="_blank"`,
     `rel="noopener noreferrer"`);
   - summary paragraph;
   - key points as a bulleted list;
   - tags row (one chip per tag);
   - category badge.

2. **`app/src/components/Section.tsx`** — renders one `Section` (feature-003 type):
   category heading + the section's cards in the order given.

3. **`app/src/components/Board.tsx`** — takes `cards: Card[]`, derives sections via the
   existing pure `groupByCategory` (feature 003), renders one `Section` per group. When
   there are no cards it renders the empty state: *"paste a link to start"*.

4. **`app/src/App.tsx`** — renders an `<h1>` app header (keeps the feature-001
   `greeting('content-digest')`) and `<Board cards={mockCards} />`.

## Rules honored

- **Render-only components.** All grouping/sorting/merging stays in the existing pure
  modules (`groupByCategory` → `resolveCategory`). Components contain no data transforms.
  The single conditional in `Board` (empty state vs. sections) is driven directly by the
  length of `groupByCategory`'s output — no computation beyond that.
- **No new pure logic, no new specs.** This slice needs no date formatting or other
  helpers; if one appears later it gets its own spec-first module under `app/src/lib/`.
  Existing specs (`greeting`, `categories`, `groupByCategory`) stay green and untouched.
- **No DOM tests.** Per working-agreement rule 5, components get no RTL layer without an
  ADR.
- **Minimal inline styles only** (constraints: no styling framework). Readability via a
  max-width container, bordered/padded/rounded card boxes, and small tag chips.

## Acceptance criteria

- GIVEN `mockCards` (7 cards) WHEN the app renders THEN the board shows the sections
  produced by `groupByCategory` — alphabetical by category, including the merged
  "AI"/"Artificial Intelligence" section — each with its category heading and its cards
  newest-first.
- GIVEN any rendered card THEN its title is an `<a href={card.url} target="_blank"
  rel="noopener noreferrer">`, and its summary, every key point, every tag, and the
  category badge are visible.
- GIVEN `<Board cards={[]} />` THEN the board renders the text "paste a link to start"
  and no sections.
- The `<h1>` header still contains "Welcome to content-digest" (feature-001 spec stays
  green).
- `npm run test:run`, `npm run lint`, and `npm run build` all pass.

## Out of scope

- `UrlInput` component (issue #3) and `lib/api.ts` fetch wrappers (issue #4).
- Loading/error states — they belong to the API-wiring slice, not the mock-driven board.
- Delete/edit interactions, drag-and-drop, category management.
- Any styling framework or shared CSS beyond minimal inline styles.

## Open questions

- None.
