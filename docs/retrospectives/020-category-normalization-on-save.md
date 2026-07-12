# Retro 020 — Category normalization on save (issue #12)

## What was built

`api/categories.py` (`resolve_category`) — a faithful Python port of feature 002's
`app/src/lib/categories.ts` — plus `db.list_categories()` (distinct labels, oldest first) and
wiring in both save paths: `POST /api/digest` and `POST /api/cards/{id}/translate` resolve the
model's free-form category against stored sections before persisting. Spec:
`docs/requirements/feature-020-category-normalization-on-save.md`.

## What worked

- **Porting the spec, not just the code.** `api/test_categories.py` mirrors every case in
  `categories.spec.ts` one-for-one, so divergence between the TS and Python implementations
  shows up as a failing named test, not a mystery board split.
- Feature 002's decision to ship the pure module with a documented rule table made the port
  mechanical — ~70 lines, first-try green.

## What didn't / surprises

- **Issue #12 assumed a frontend call site** ("invoke resolveCategory at card-save time"), but
  by feature 011 the save path had moved into the backend — so the wiring became a port, not
  an import. Cross-language duplication is the accepted cost; the mirrored spec is the sync
  mechanism. Lesson: an issue's "remaining work" note goes stale when the architecture moves
  under it — re-derive the call site from the current code, not the issue thread.
- Adding a collaborator to a route (`list_categories`) broke 16 existing route specs until the
  monkeypatch wirings gained the new stub. That is the seam style working as intended, but the
  fan-out edit across three spec files is the same smell retros 016/017 flagged: a shared
  route-wiring fixture (like `happy_wiring`, but reused across files via `conftest.py`) would
  have made this a one-line change.

## Workflow changes

- None to the working agreement. The `conftest.py` shared-wiring idea joins the existing
  "shared `makeCard` spec factory" backlog item rather than a new rule — next backend spec
  touch should do both.
