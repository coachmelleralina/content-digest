# Retro 003 — card-model

**Feature:** [feature-003-card-model](../requirements/feature-003-card-model.md) (issue #1)

## What we did

`Card`/`Section` types in `app/src/types.ts` mirroring the PLAN `cards` table, 7 realistic
mock cards across 4 categories in `app/src/mocks/cards.ts`, and a pure
`app/src/lib/groupByCategory.ts` (alphabetical sections, newest-first cards), spec-first:
red run captured (`Cannot find module './groupByCategory'`), then 21/21 green, lint clean.

## What worked

- Reusing `resolveCategory` (feature 002) inside `groupByCategory` cost one import and one
  call, and the "single remaining call site" note in the 002 retro made the integration
  decision instant — the board grouping path is now normalization-aware before any UI exists.
- Putting one near-duplicate category pair ("AI" / "Artificial Intelligence") directly into
  the mock fixtures means the merge behavior will be visible the moment the board renders,
  not just in specs.
- Speccing the fixtures themselves (count, field shape, ≥3 resolved categories) keeps future
  mock edits from silently breaking the board's demo state.

## Friction

- Issue #1 referred to the feature-002 export as `normalizeCategory`; the actual export is
  `resolveCategory(raw, existing)`. Trivial here, but stale API names in issues cost a
  lookup — issues should quote real signatures once code exists.
- The 002-flagged `npm run build` TS 6 `baseUrl` failure was fixed in `48a7ab7` before this
  feature, so no build friction remained — flagging it in the prior retro worked as intended.

## Changes

- None to the working agreement. Suggested "Current state" addition for the orchestrator:
  data layer for PLAN build step 1 (types + mocks + `groupByCategory`) done; next slice is
  the render-only board components consuming `mockCards`.
