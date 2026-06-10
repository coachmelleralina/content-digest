# Retro 007 — api-client

**Feature:** [feature-007-api-client](../requirements/feature-007-api-client.md) (issue #4)

## What we did

Typed mock-backed API client: `app/src/lib/apiError.ts` (`ApiError extends Error`,
displayable message + optional HTTP status) and `app/src/lib/api.ts` exporting
`digestUrl`/`listCards`/`deleteCard` shaped exactly like the future `/api/*` routes. The
exports delegate to an internal `Backend` interface; the only implementation today is an
in-memory mock seeded from `mockCards`, so issue #10 swaps mock→fetch in one internal layer
without touching exported signatures. Spec-first: red run captured
(`Cannot find module './apiError'`), then 33/33 green, lint clean, build clean.

## What worked

- The internal `Backend` interface made "mock today, fetch tomorrow" a non-decision: the
  spec's compile-time signature checks pin the contract, and the mock is created by one
  factory function the fetch implementation will replace.
- Reusing `resolveCategory` (feature 002) in the mock's digest path means the save-path
  normalization the 002 doc anticipated is now exercised end-to-end in specs before any
  backend exists — and the "re-resolving the returned category is a no-op" assertion tests
  the integration without hardcoding which category the fake AI picks.
- The `fail.example.com` rejection hostname gives issues #2/#3 a deterministic way to build
  and demo UI error states with zero test scaffolding.

## Friction

- The issue's requested `constructor(message: string, public status?: number)` parameter
  property is rejected by the app tsconfig: `erasableSyntaxOnly` is enabled (Vite template
  default for type-stripping compatibility) and `tsc -b` fails with TS1294. Kept the config
  (working agreement: never loosen TS strictness) and used an explicit `status?: number`
  field — identical public shape. Lesson: issue snippets should be checked against
  `erasableSyntaxOnly` (no parameter properties, no enums, no namespaces).
- `vitest run` passed the spec while `npm run build` failed on the same syntax — tests alone
  don't catch erasable-syntax violations because Vite strips types without `tsc`. Running
  the full test/lint/build trio before committing caught it; keep doing that.
- The mock store needs reseeding between specs, which forced a fourth export
  (`resetApiMock`) beyond the three-op contract. Accepted as a clearly-marked test-only wart
  that gets deleted with the mock in issue #10.

## Changes

- None to the working agreement (the test/lint/build-before-commit habit already covers the
  erasable-syntax gap). Suggested `CLAUDE.md` "Current state" line for the orchestrator:
  typed mock-backed API client (feature 007 / issue #4) done — `lib/api.ts` is the single
  frontend↔backend boundary for issues #2/#3 to consume; issue #10 replaces only its
  internal mock backend with fetch.
