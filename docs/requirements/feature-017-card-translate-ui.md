# Feature 017 — Per-card translate UI (issue #16)

## User story

- As a reader, I want to translate a card RIGHT ON the card (UA/RU/EN switcher next to the
  article, no app-wide language setting), so that I translate only when and what I want (PRD).

## Backend contract (built in parallel by issue #14 — code against it exactly)

- `POST /api/cards/{id}/translate` with body `{"language": "uk" | "ru" | "en"}` →
  `200` with the **full updated card JSON**, including `language`. `keyPoints` stay
  `{takeaway, quote}` objects and quotes remain in the original article language, so
  takeaway text-fragment deep links keep working after translation.
- Errors arrive as the usual `{detail}` body: `404` unknown card, `422` bad language, `5xx`.
- Cards from `POST /api/digest` and `GET /api/cards` now include `language`.

## Data model change

`Card` gains `language: string` (the card's current display language, e.g. `'uk'`). Mock
fixtures and the mock card generator get `language: 'uk'`.

## Acceptance criteria

**Pure modules (spec-first):**

- `lib/languages.ts` (new):
  - `SUPPORTED_LANGUAGES = ['uk', 'ru', 'en'] as const` and the derived `Language` type.
  - `languageLabel(code): string` — `uk → 'UA'`, `ru → 'RU'`, `en → 'EN'`.
  - `isSupportedLanguage(s): s is Language` — `true` for the three codes, `false` for
    anything else (`'de'`, `''`, `'UK'`).
- `lib/api.ts` — new export `translateCard(id: string, language: Language): Promise<Card>`:
  - HTTP backend: `POST /api/cards/{id}/translate` with JSON body `{language}`; parses the
    updated card on 200; maps `{detail}` errors to `ApiError` with status (same `request`
    helper as the other routes).
  - Mock backend: finds the card, flips `language`, prefixes `summary` with `[${language}] `
    (visible-change stand-in for real translation), keeps everything else, persists the
    updated card in the store; unknown id → `ApiError('Card not found', 404)`.
  - `digestUrl` signature UNCHANGED; mock `generateCard` emits `language: 'uk'`.

**UI (components stay render-only — decisions via props and pure helpers):**

- `Card.tsx` shows a compact switcher near the category badge: three small buttons
  UA | RU | EN (labels via `languageLabel`, order via `SUPPORTED_LANGUAGES`).
- The button for the card's current `language` is highlighted (same visual treatment as the
  active tag chip) and disabled — clicking the current language is a no-op (no callback).
- Clicking another language calls `onTranslate(card.id, lang)`.
- New pass-through prop `translatingId: string | null` (App → Board → Section → Card; chosen
  over a per-card boolean so the single piece of state lives in App and components only
  compare ids). While `translatingId === card.id` the whole switcher is disabled and a busy
  hint `…` is shown next to it.
- `App.tsx` `handleTranslate(id, language)`: set `translatingId` → `translateCard` → replace
  the card in `cards` state (the board regroups naturally if the category changed) → clear
  `translatingId`. Errors go to the existing `boardError` line via `toErrorMessage`, and
  `translatingId` is cleared.

## Out of scope

- App-wide language picker / default-language setting — explicitly rejected (per-card only).
- Backend translate endpoint itself — issue #14 (parallel); here it is stubbed in specs.
- `UrlInput.tsx` and `api/` — untouched.
- Full e2e against the deployed translate endpoint — after #14 lands (mock + stubbed-fetch
  coverage here).
