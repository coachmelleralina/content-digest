# Feature 014 — ELI5 digest: explain-for-a-child prompt, grounded takeaways, canonical tags, language param (issue #13)

## Story

As a reader (PRD, revised digest scenarios 2026-06-11), I want each card to EXPLAIN the article
in very simple language — what it is about and which thoughts I take away — with each takeaway
grounded in a verbatim quote from the source (the future text-fragment deep link, issue #16),
canonical reusable topic tags (the future tag filter, issue #15), and the digest language
selectable per request (the future per-card translation, issue #14).

## Scope

`api/digest.py` (prompt + models + post-parse verification/normalization), `api/index.py`
(`language` in the request body, `keyPoints` object mapping), and their specs. No frontend
changes (issues #14–#16), no DB changes (`key_points` is already jsonb).

## Acceptance criteria

1. **ELI5 explanation.** The system prompt instructs the model to EXPLAIN the article in 2–4
   sentences in simple words, "like to a child": what it is about and why it matters. No
   jargon; unavoidable terms must be explained in brackets. `summary` validation unchanged
   (non-empty).
2. **Grounded takeaways.** `key_points` becomes a list of objects. Pydantic:
   `KeyPoint { takeaway: str (non-empty, stripped), quote: str | None }`,
   `Digest.key_points: list[KeyPoint]` (1..8 accepted; the prompt asks for 3–5). The prompt
   requires per item:
   - `takeaway` — a practical "what I take with me" thought, simply worded, in the digest
     language;
   - `quote` — a SHORT (≤12 words) VERBATIM fragment copied EXACTLY, character for character,
     from the article text, in the article's ORIGINAL language (no paraphrase, no translation).
3. **Code-side quote verification.** After parsing, each quote is checked against the source
   text with whitespace-normalized comparison (`" ".join(s.split())` on both sides). A quote
   that does not occur in the source is replaced with `quote = None`; the takeaway is kept.
   Exposed as a pure helper (`verify_quotes`) and applied inside `digest_text`.
4. **Canonical tags.** The prompt asks for 2–4 canonical topic tags: lowercase single general
   concepts (e.g. "продуктивність", "ai", "здоров'я"), reusable across articles — broad topics
   preferred over phrases lifted from the text. Code normalizes regardless of model behavior:
   strip, lowercase, truncate each tag to ≤24 chars, drop empties, keep at most 4 (truncate
   the list, never reject). Pure helper (`normalize_tags`) applied via the `Digest` validator.
5. **Language parameter.** `digest_text(text, title=None, *, language="uk", client=None)`;
   allowed values `uk` / `ru` / `en`, anything else raises `ValueError` before any HTTP call.
   The system prompt names the target language: explanation + takeaways in that language,
   quotes stay in the article's original language. `build_system_prompt(language)` is an
   exported, unit-tested pure helper.
6. **Route.** `POST /api/digest` body is `{url, language?}` with
   `language: Literal["uk","ru","en"] = "uk"` (other values → 422 via pydantic). The route
   passes `language` through to `digest_text` and maps `key_points` →
   `keyPoints: [{takeaway, quote}, ...]` (camelCase list of objects).
7. **Category unchanged** (free-form, single line, ADR 004).
8. **Specs first, all MockTransport / monkeypatch, no network.** `api/test_digest.py`:
   prompt-builder assertions (ELI5, language, exact-quote, canonical-tag instructions),
   quote verification (found → kept, not found → None, whitespace-normalized match),
   tag normalization (uppercase → lower, >4 truncated, >24-char tag truncated),
   `KeyPoint` validation. `api/test_digest_route.py`: language default `uk`, bad language →
   422, `keyPoints` object mapping. Existing tests updated to the new shape; full pytest green.
9. **Live smoke** (module-level, no route/DB): real article → `digest_text(language="uk")` →
   simple Ukrainian explanation, ≥1 quote survives verification, lowercase canonical tags.
   Output recorded in the retro.

## Out of scope

- Per-card translation UI / endpoint — issue #14.
- Tag-click filtering — issue #15.
- Clickable takeaways building `#:~:text=` deep links in the frontend — issue #16.
- Re-digesting existing cards to the new shape (old cards keep string keyPoints in the DB).

## Notes

- Quotes are verified against the **full** original text (the prompt sees the truncated text,
  which is a subset, so verification can only be more permissive — never drops a quote the
  model legitimately copied from the prompt).
- The response shape change (`keyPoints` strings → objects) is a contract change for the
  frontend; issue #16 consumes `{takeaway, quote}` to build text-fragment links.
