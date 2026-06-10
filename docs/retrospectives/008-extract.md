# Retro 008 — extract.py: URL → readable article text (issue #6)

## What was built

`api/extract.py`: pure `extract_article(html, url) -> ExtractedArticle {title, text}` on
**trafilatura 2.x**, typed errors (`ExtractionError` → `FetchError` / `NotHtmlError` /
`EmptyExtractionError`, all with user-displayable `message`), `fetch_html` (httpx, redirects,
timeout) and `extract_from_url` composing both. 10 new tests on 3 HTML fixtures + MockTransport;
full suite 11/11 green on Python 3.12.

## What worked

- **Spec-first held cleanly**: requirements doc → failing import (red) → implementation →
  green on the first run. Writing acceptance criteria as concrete fixture assertions made the
  test file almost mechanical to produce.
- **trafilatura over readability-lxml** was the right call: one library gives both main-text
  and metadata (title), so the `<title>`-tag fallback regex is only a second-line defense.
- **`transport` test seam** on `fetch_html` (httpx `MockTransport`) let the error mapping
  (non-200, non-HTML content-type, network error) be tested with zero network — fetch tests
  did NOT need to be deferred to issue #8.
- **`MIN_TEXT_CHARS = 120` guard**: trafilatura happily returns tiny strings for paywall
  shells; a minimum-length cutoff is what actually enforces the PRD "never a blank card" rule.

## What didn't / friction

- The issue text allowed leaving fetch error-mapping tests to #8; doing them now was cheap
  and removes a tail risk from #8 — worth defaulting to "test the seam immediately" when a
  MockTransport-style fake exists.
- Realistic fixtures take care: trafilatura ignores pages with too little body text, so
  fixtures needed several full paragraphs before the "happy path" tests would pass.
- Git author identity in worktree sessions is auto-derived (hostname email); harmless locally
  but worth setting `user.email` once globally.

## Workflow changes proposed

- None requiring `CLAUDE.md` edits beyond the routine state/log update — which is **deferred
  to merge time** because parallel feature agents (005–009) would all collide on `CLAUDE.md`;
  the integrating session should add this retro to the Self-improvement log and refresh
  "Current state".

## Notes for issue #8 (route wiring)

- Call `extract_from_url(url)`; catch `ExtractionError` and return `e.message` with an
  appropriate status (FetchError → 502/400, NotHtmlError/EmptyExtractionError → 422).
- `fetch_html`'s `transport` kwarg is a test seam only — never set it in route code.
- `httpx` was already a runtime dep; only `trafilatura>=2.1` was added to requirements.txt.
