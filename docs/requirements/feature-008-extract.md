# Feature 008 — `api/extract.py`: URL → readable article text (issue #6)

## Goal

A pure, tested extraction module that turns an article URL into `{ title, text }`, with typed
errors so the API layer (issue #8) can always return a clear message — per the PRD rule:
**never a blank/broken card**.

## Library choice

**trafilatura** (`>=2.1`) — pure-Python, robust main-content extraction with built-in metadata
(title) support and better benchmark precision/recall than readability-lxml; no system deps
beyond lxml wheels. PLAN already sanctions "readability/trafilatura", so no new ADR is needed.

## API

All in `api/extract.py`:

- `ExtractedArticle` — frozen dataclass `{ title: str, text: str }`.
- `ExtractionError(Exception)` — base; carries a user-displayable `message`.
  - `FetchError` — URL unreachable, non-200 response, timeout, or non-HTML content-type.
  - `NotHtmlError` — the supplied payload is not HTML (e.g. JSON, PDF bytes, plain junk).
  - `EmptyExtractionError` — HTML parsed but no usable article text (paywall, empty page,
    nav-only shell).
- `extract_article(html: str, url: str) -> ExtractedArticle` — **pure, no network**.
  - Raises `NotHtmlError` when the input doesn't look like HTML.
  - Raises `EmptyExtractionError` when no meaningful body text is found.
  - Title falls back to the `<title>` tag when trafilatura's metadata finds none; falls back
    to the URL's host as a last resort (a card must always have a non-empty title).
- `fetch_html(url: str, timeout: float = 10.0, transport=None) -> str` — httpx GET, follows
  redirects (`transport` is a test seam for `httpx.MockTransport`; never set in production).
  - Raises `FetchError` on network errors, timeouts, non-2xx status, or a `Content-Type`
    that is not HTML (`text/html` / `application/xhtml+xml`).
- `extract_from_url(url: str) -> ExtractedArticle` — `extract_article(fetch_html(url), url)`.

## Acceptance criteria

Spec-first pytest in `api/test_extract.py`, fixtures in `api/fixtures/` (no network in tests):

1. `article.html` (realistic article page): `extract_article` returns the article title and
   body text; boilerplate (nav, footer) is not the dominant content.
2. `nav_heavy.html` (nav/sidebar/footer-heavy page with a real article inside): the article
   body still extracts; the returned text contains the article's sentences.
3. `junk.html` (page with no article content): raises `EmptyExtractionError`.
4. Non-HTML input (e.g. a JSON string): raises `NotHtmlError`.
5. Title fallback: a page where extraction metadata yields no title falls back to `<title>`.
6. All errors derive from `ExtractionError` and expose a non-empty user-displayable `message`.

`fetch_html` error mapping (network) is exercised with `httpx.MockTransport` — still no real
network. Full route wiring (`POST /api/digest`) is **out of scope** — that's issue #8.

## Out of scope

- Wiring into `api/index.py` routes (issue #8).
- AI digest (`digest.py`, issue #7), persistence (db), frontend.
