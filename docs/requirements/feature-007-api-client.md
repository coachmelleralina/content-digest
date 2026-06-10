# Feature 007 — Typed API client `lib/api.ts` (mock-backed)

Tracks GitHub issue [#4](https://github.com/coachmelleralina/content-digest/issues/4).
Part of PLAN build step 1 ("Frontend shell, no AI yet"): the single typed boundary between
the frontend and the future `/api/*` backend, backed by an in-memory mock today so the board
UI (issues #2/#3) can be built and demoed before the real HTTP layer lands (issue #10).

## User story

As the board's only user, I want pasting a URL, loading my cards, and deleting a card to go
through one typed API layer with clear, displayable errors, so the UI works identically today
(mocks) and after the backend is wired in — with zero component changes.

## Scope

1. **`app/src/lib/apiError.ts`** — the error type every API op rejects with:

   ```ts
   export class ApiError extends Error {
     constructor(message: string, public status?: number);
   }
   ```

   `message` is always user-displayable (the UI may render it verbatim); `status` carries the
   HTTP status code when one applies.

2. **`app/src/lib/api.ts`** — the ONLY frontend↔backend boundary. Exports exactly:

   ```ts
   digestUrl(url: string): Promise<Card>;   // future: POST /api/digest {url} → card JSON
   listCards(): Promise<Card[]>;            // future: GET /api/cards
   deleteCard(id: string): Promise<void>;   // future: DELETE /api/cards/{id}
   ```

   Internally the three exports delegate to a `Backend` interface with the same three ops.
   Today the only implementation is an in-memory mock; issue #10 replaces it with a
   fetch-based implementation — swapping that ONE internal layer, never the exported
   signatures. A test-only `resetApiMock()` export reseeds the mock between specs and is
   deleted together with the mock in issue #10.

## Mock behavior

- **State.** The backend holds an in-memory card list seeded from a copy of `mockCards`
  (feature 003). The fixtures themselves are never mutated.
- **`listCards()`** resolves with a copy of the current list (callers can't mutate the store).
- **`digestUrl(url)`** simulates ~300 ms network+AI latency, then resolves with a plausible
  generated `Card`: `id` via `crypto.randomUUID()`, `createdAt` now (ISO 8601), `title`
  derived from the URL slug, non-empty `summary`/`keyPoints`/`tags`, and `category` resolved
  via `resolveCategory` (feature 002) against the categories already in the store — exactly
  where the save path normalizes labels per the 002 feature doc. The new card is added to the
  store (the real backend persists, PLAN step 3), so a subsequent `listCards()` includes it.
  - URL whose hostname is **`fail.example.com`** → rejects `ApiError("Could not extract this
    article", 422)` so UI error paths are testable.
  - Unparseable URL → rejects the same `ApiError` 422 (never a partial card, per PLAN step 2).
- **`deleteCard(id)`** removes the card from the store; unknown `id` rejects
  `ApiError("Card not found", 404)`.

## Acceptance criteria

- `listCards()` resolves with the 7 seeded mock cards initially; mutating the resolved array
  does not affect a later `listCards()` result.
- `digestUrl(url)` resolves with a `Card` whose keys match the `Card` type shape **exactly**
  (no missing, no extra), with a UUID `id`, valid ISO `createdAt`, the input `url`, and
  non-empty title/summary/keyPoints/tags/category.
- The generated `category` is already board-resolved: re-resolving it against the pre-call
  categories returns the same label.
- `digestUrl` takes ≥ ~250 ms (simulated latency) and appends the card to the store.
- `digestUrl("https://fail.example.com/...")` rejects with `ApiError`, message
  `"Could not extract this article"`, `status` 422. Nothing is added to the store.
- `deleteCard(id)` removes exactly that card; deleting an unknown id rejects with `ApiError`
  404 and leaves the store unchanged.
- `ApiError` is an `Error` (`instanceof` both), `name === 'ApiError'`, optional `status`.
- All rejections crossing the boundary are `ApiError` instances.

## Out of scope

- React components and any `App.tsx` change (issues #2/#3 own those).
- The real fetch/HTTP implementation (issue #10) and any backend (`api/`) work.
- Persistence across reloads; the mock store is per-page-load memory only.
- New runtime dependencies (none needed; `crypto.randomUUID` is a web platform API).
