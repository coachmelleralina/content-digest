# Retrospective 018 — Live bug reports: slow translate (500) + dead takeaway links

## What we did

User reported (with screenshot): takeaway deep links don't scroll/highlight in Chrome, and
translation is very slow — one success, then `Request failed (HTTP 500)`.

**Slowness/500 — root cause found via phase timing in prod logs:** `extract=0.6s ai=176.8s`.
The identical OpenRouter call takes ~8s locally — Vercel-egress traffic was being routed by
OpenRouter to a slow provider (~20× slower). Fixes, verified live:
- `digest.py`: `"provider": {"sort": "latency"}` in the payload (spec-first, red→green).
- `OPENROUTER_MODEL=anthropic/claude-haiku-4.5` set in Vercel env (newer/faster, noticeably
  better Ukrainian/Russian — ADR 004 one-line swap as designed).
- `maxDuration: 300` in vercel.json as a safety net.
- Result: translate went **136–178s → 8–9.5s** on two consecutive prod runs. The user's 500
  was the slow path hitting the platform limit; the generic (non-`{detail}`) message confirms
  it came from the platform, not our handlers.

**Takeaway links — two real defects fixed:**
- `fragmentUrl.ts`: `encodeURIComponent` leaves `-` unescaped, but a dash is special in the
  `#:~:text=` directive — one dash anywhere broke the whole link. Now `%2D`-escaped (specced).
- `digest.py verify_quotes`: quotes like `- Assign roles…` carried list markup from the
  extracted text that the rendered DOM doesn't contain — marker is now stripped before
  verification (specced).
- Confirmed byte-level (curl + repr) that current quotes exist verbatim in habr's HTML (no
  NBSP mismatch).

## What didn't / open

- **Full click-through verification of highlights is pending.** Programmatic navigation
  (extension `navigate`) does not trigger text-fragment highlighting even for trivially
  present text — Chrome appears to require real user activation, so our tooling cannot fully
  reproduce a human click; the session also hit its usage limit mid-verification. The user
  must re-test by clicking a takeaway. If habr still doesn't highlight: next hypothesis is
  quotes crossing inline-markup boundaries → switch to shorter `textStart` prefixes (≤6 words)
  or `textStart,textEnd` syntax.
- SPA-rendered targets (developer.harness.io docs) likely never highlight — content hydrates
  after navigation. Graceful degradation (article opens at top) is accepted.
- PHASE-TIMING prints left in routes intentionally — cheap, and they just paid for themselves.

## Changes to CLAUDE.md / constraints

- Linked this retro. No workflow changes — but note: live phase timing in logs found in
  minutes what local profiling could not (env-specific perf bug).
