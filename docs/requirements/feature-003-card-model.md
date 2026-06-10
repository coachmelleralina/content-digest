# Feature 003 — Card data model + mock fixtures + groupByCategory

Tracks GitHub issue [#1](https://github.com/coachmelleralina/content-digest/issues/1).
First slice of PLAN build step 1 ("Frontend shell, no AI yet"): the data layer the board
components will render — types, realistic mock cards, and the pure grouping logic.

## User story

As the board's only user, I want my saved article cards organized into topic sections —
sections in a predictable alphabetical order, newest articles first within each section — so
I can scan recent reading by topic without hunting through an unordered pile.

## Scope

1. **`app/src/types.ts`** — shared frontend types:

   ```ts
   export type Card = {
     id: string;
     url: string;
     title: string;
     summary: string;
     keyPoints: string[];
     tags: string[];
     category: string;
     createdAt: string; // ISO 8601
   };

   export type Section = { category: string; cards: Card[] };
   ```

   `Card` mirrors the `cards` table in [PLAN.md](../PLAN.md) (`key_points`/`tags` jsonb →
   arrays, `created_at` → ISO string).

2. **`app/src/mocks/cards.ts`** — 6–8 realistic mock cards (real-sounding titles, summaries,
   key points, tags) spread across 3+ categories, including at least one near-duplicate
   category label pair so grouping behavior is visible in the UI later.

3. **`app/src/lib/groupByCategory.ts`** — pure module:

   ```ts
   groupByCategory(cards: Card[]): Section[]
   ```

## Behavior of `groupByCategory`

- Cards are filed into sections by category, **reusing `resolveCategory` from
  `app/src/lib/categories.ts` (feature 002)**: each card's raw category is resolved against
  the section labels created so far (in input order), so near-duplicate labels
  ("startups" vs "Startup", "AI" vs "Artificial Intelligence") land in **one** section. The
  first-seen card's cleaned label names the section. **Yes — feature 002 is reused**; this is
  the "single remaining call site" the 002 feature doc anticipated (board grouping rather
  than the save path, which still gets its own wiring in issues #9/#10).
- Sections are sorted **alphabetically by category** (case-insensitive, locale-aware).
- Within a section, cards are sorted **newest-first by `createdAt`** (ISO strings compared as
  timestamps).
- Empty input returns `[]`.
- Pure: the input array and card objects are never mutated.

## Acceptance criteria

- `groupByCategory([])` → `[]`.
- Cards sharing a category form one section; section count equals distinct (resolved)
  categories.
- Section order is alphabetical regardless of input order.
- Card order inside a section is newest-first by `createdAt` regardless of input order.
- Near-duplicate category labels (case/whitespace, plural, acronym, typo — per feature 002
  rules) merge into a single section keeping the first-seen label.
- Input array order and contents are unchanged after the call (no mutation).
- Mock fixtures: 6–8 cards, ≥3 distinct resolved categories, every `Card` field populated
  with realistic content (no lorem ipsum), valid ISO `createdAt` values.

## Out of scope

- React components (`Board`, `Section`, `Card`, `UrlInput`) — next slice of build step 1.
- `lib/api.ts` fetch wrappers and any backend (`/api/*`) work.
- Persistence; mocks are static in-memory fixtures only.
- Category renaming/management UI.
