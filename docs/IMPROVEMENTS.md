# Improvements & Refactor Plan — content-digest (2026-06-11)

A combined product review, engineering review, and prioritized backlog after the v2 release
(features 014–017 live at https://content-digest.vercel.app). Source: full-codebase review +
live prod verification. This is a planning doc — each P0/P1 item should become a spec-first
feature (`docs/requirements/feature-*.md`) before implementation.

## Where the product stands today

**Works, live, prod-verified:** paste URL → ELI5 explanation (uk/ru/en) with grounded
takeaways that deep-link to the exact passage; canonical clickable tags that filter the board;
topic sections; per-card UA|RU|EN translation; delete; Neon persistence. 95 vitest + 111 pytest
green. Digest/translate ~8–9s after the latency-routing fix.

## Problem Statement

The MVP is feature-complete but has three classes of gap that matter now that it is **public**:
(1) a public, unauthenticated endpoint spends the owner's OpenRouter balance with no limit;
(2) the server fetches arbitrary user URLs (SSRF surface) and mishandles malformed ids; (3) the
UX has rough edges (misleading errors, no first-run guidance, slow cold path) that cost trust.
Left unsolved: runaway cost/abuse risk, a security hole, and avoidable user confusion.

## Goals

1. **Cap abuse cost:** no single client can run more than N digests/translates per window;
   measured by the rate-limit rejection working in prod.
2. **Close the security holes:** private-IP/loopback URLs rejected; malformed ids return 404;
   oversized inputs rejected — verified by new tests + a prod probe.
3. **Make failures honest:** every user-visible error says what actually happened (no "database
   unavailable" for a bad id).
4. **Smooth the first run & the wait:** an empty board explains itself; long digests show
   progress, not a frozen button.
5. **Pay down the flagged tech debt** (shared test factory, type-safety on `language`, dead
   bootstrap module) so future features move faster.

## Non-Goals (this round)

1. **No accounts/auth** — still out of scope; rate limiting is by IP/edge, not login.
2. **No search or full-text** — tags + sections remain the only navigation (PRD non-goal holds).
3. **No styling-framework migration** — inline-style dedup waits for a styling ADR; not now.
4. **No multi-user/shared boards** — single-user product unchanged.
5. **No new capture surfaces** (extension, RSS) — validate the core loop first.

## User Stories

**Owner (cost & safety)**
- As the owner, I want a per-IP rate limit so that a stranger can't drain my OpenRouter balance.
- As the owner, I want the server to refuse internal/private URLs so that the app can't be used
  to probe cloud metadata or my network.

**Reader (trust & clarity)**
- As a reader, when I (or a stale tab) act on a card that no longer exists, I want a clear "not
  found" message, not a scary "database unavailable".
- As a reader opening the app for the first time, I want the empty board to tell me what to do.
- As a reader waiting on a digest, I want to see it's working (and roughly how long), so I don't
  think it froze.
- As a reader, I want a way to retry a digest/translate that failed without re-pasting.

## Requirements

### Must-Have (P0) — ship next

- **P0-1 Rate limiting on `POST /api/digest` and `/translate`** (security S1).
  - Given more than N requests from one IP in the window, when the next arrives, then it gets
    429 with a clear `{detail}` and the frontend shows "слишком много запросов, попробуйте позже".
  - Tech note: Vercel functions are stateless → needs Vercel KV / Upstash Redis (ADR required;
    adds a runtime dependency). Start with a conservative N (e.g. 10/min, 100/day per IP).
- **P0-2 Malformed-id → 404, not 500** (bug B1, confirmed live).
  - Given a non-UUID `card_id` to DELETE or translate, then the response is 404 "Card not
    found.", and the DB is never queried. Add the guard at the route layer + tests (T1).
- **P0-3 SSRF: reject private/loopback/link-local URLs** (security S2).
  - Given `http://169.254.169.254/…`, `http://10.x`, `http://192.168.x`, `http://127.x`,
    `0.0.0.0`, when posted to `/api/digest`, then 422 before any fetch. Resolve host → check
    against RFC-1918/link-local/loopback ranges. Tests T3.
- **P0-4 Input size limits** (security S3).
  - `DigestRequest.url` gets `Field(max_length=2048)`; oversized body → 422. Cheap, no deps.

### Nice-to-Have (P1) — fast follow

- **P1-1 `update_card` rowcount check** (bug B3): translate after a concurrent delete currently
  "succeeds" silently and returns a card that isn't in the DB. Check `rowcount`, raise → 404/409.
- **P1-2 Honest, friendlier error copy:** map backend `{detail}` to localized, non-technical
  messages; today the board shows raw English "Request failed (HTTP 500)".
- **P1-3 Empty-board first-run state:** replace the bare board with a short "вставь ссылку на
  статью — получишь простое объяснение" hint + maybe one example.
- **P1-4 Progress feedback on digest/translate:** the Digest button and per-card translate
  already disable, but add an explicit "это займёт ~10 сек" hint and a spinner; consider a
  client-side timeout with a retry affordance.
- **P1-5 `language: Language` type** (refactor R4): tighten `Card.language` from `string` to the
  `Language` union so the switcher can't silently fail on an unexpected value.

### Future Considerations (P2)

- **P2-1 Shared test factories** (refactor R1/R6): `makeCard` in `app/src/lib/testHelpers.ts` +
  `make_card`/`_raise` in `api/conftest.py`. Five fixtures drift today; flagged in retros 016/017.
- **P2-2 Remove `resetApiMock` from the production module** (refactor R2): build a fresh
  `createMockBackend()` per spec instead of a test-only export on `lib/api.ts`.
- **P2-3 Delete vestigial `greeting.ts`/`.spec.ts`** (refactor R3): inline the one string in App.
- **P2-4 Move/merge near-duplicate AI categories on save** (existing issue #12): the
  `resolveCategory` module exists but isn't wired into the save path.
- **P2-5 GitHub→Vercel auto-deploy** (deploy backlog): connect the repo so `git push` deploys.
- **P2-6 Better Ukrainian quality knob:** document that `OPENROUTER_MODEL` swaps the model; pick
  a default that minimizes russisms once observed at volume.

## Success Metrics

*Solo/early product — measured by prod probes + observation, not analytics tooling.*

**Leading:**
- 0 successful requests above the rate limit (probe: N+1 requests → last is 429).
- 100% of malformed-id and private-URL requests rejected with the correct status (probe suite).
- Digest/translate p50 ≤ 12s, p95 ≤ 25s on the warm path (the latency fix already lands ~9s).
- 0 user-visible "HTTP 500"/raw-English errors on expected failure paths.

**Lagging:**
- OpenRouter spend stays within an expected ceiling (no abuse spikes) over a month.
- The owner stops hitting confusing errors during normal use (qualitative).

## Open Questions

- **[eng — blocking P0-1]** Rate-limit store: Vercel KV vs Upstash Redis vs Vercel's built-in
  firewall rules? Each is a new dependency → ADR. Cheapest path that survives cold starts?
- **[eng — blocking P0-3]** SSRF check on DNS resolution: resolve at validation time and also at
  fetch time (TOCTOU)? Or use an egress allowlist? Decide in the feature's ADR.
- **[product — non-blocking]** First-run hint copy + whether to ship a sample card.
- **[eng — non-blocking]** Is a 10s+ digest acceptable UX long-term, or should we stream partial
  results / move to a faster model by default?

## Timeline / Phasing

- **Phase 1 (security & correctness, P0):** P0-2 + P0-4 are tiny and depend on nothing — do
  first. P0-3 (SSRF) next. P0-1 (rate limit) last in the phase because it needs an ADR + a new
  dependency. All four are parallelizable except the shared ADR for P0-1/P0-3.
- **Phase 2 (UX polish, P1):** P1-1..P1-5, mostly independent; frontend (P1-2/3/4/5) and backend
  (P1-1) split cleanly into two parallel tracks like the prior waves.
- **Phase 3 (debt, P2):** opportunistic; do P2-1/2/3 the next time those files are touched.
