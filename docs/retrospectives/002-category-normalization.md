# Retro 002 — category-normalization

**Feature:** [feature-002-category-normalization](../requirements/feature-002-category-normalization.md) (issue #12)

## What worked

- Picking a backlog item ahead of its dependencies was viable because the issue's logic is
  pure: the module + spec landed with zero coupling to the not-yet-built save path. The
  "logic in pure modules" rule paid off before any UI exists.
- Rule-priority design (fold → plural → acronym → typo) made each spec case map to exactly one
  rule, so the failing-test-first loop was fast.
- Encoding the *negative* acceptance criterion ("Art" vs "AI" must not merge) as a spec caught
  the need for length guards on the typo rule immediately.

## What didn't

- `npm run build` fails on clean HEAD: TS 6.x deprecates `baseUrl` in `tsconfig.app.json`
  (TS5101). Pre-existing, out of scope here per "no unscoped refactors" — needs its own small
  fix commit.
- Issue #12 says "normalization on save", which can't be fully closed until issues #9/#10
  exist. The issue text didn't distinguish "pure logic" from "wiring" sub-tasks.

## Workflow changes

- When a backlog issue mixes pure logic with integration, deliver the pure module first and
  leave the issue open with a comment naming the single remaining call site — recorded in the
  feature doc ("Wiring … out of scope here").
- No CLAUDE.md/constraints changes needed beyond the Current state update (done in the feature
  commit).
