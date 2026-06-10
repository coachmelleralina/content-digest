# Feature 002 — Category normalization (near-duplicate merge)

Tracks GitHub issue [#12](https://github.com/coachmelleralina/content-digest/issues/12).

## Problem

Categories are free-form, AI-chosen ([ADR 004](../decisions/004-openrouter-ai.md)). The model
can produce near-duplicate labels — "AI" vs "Artificial Intelligence", "Startups" vs
"Startup", "machine  learning" vs "Machine Learning" — which split the board into redundant
sections.

## Scope

A **pure module** `app/src/lib/categories.ts` exposing:

```ts
resolveCategory(raw: string, existing: string[]): string
```

Given the AI-proposed label and the list of category labels already present on the board, it
returns the label to file the card under: an existing label when the new one is a
near-duplicate, otherwise the cleaned-up new label (which becomes a new section).

Wiring into the save path is **out of scope here** — it happens when the save flow exists
(issues #9/#10). This module is the single call site dependency for that work.

## Matching rules (in priority order)

1. **Fold + exact.** Trim, collapse inner whitespace, treat `-`/`_` as spaces, compare
   case-insensitively. `" machine  learning "` matches existing `"Machine Learning"`.
2. **Singular/plural.** Trailing `s` on the last word is ignored (words of ≥4 chars only, so
   short labels are never mangled). `"Startups"` matches `"Startup"`.
3. **Acronym.** A short label matches a multi-word label whose initials spell it, in either
   direction. `"AI"` matches `"Artificial Intelligence"`; `"Artificial Intelligence"` matches
   existing `"AI"`.
4. **Typo tolerance.** Levenshtein distance ≤1 (≤2 for labels of ≥8 chars), only for labels of
   ≥5 chars — short labels like `"Art"` vs `"AI"` must NOT merge.

On a match, the **existing** label is returned verbatim, so the section keeps its original
name and never splits. With no match, the trimmed/whitespace-collapsed raw label is returned
with its original casing. Empty/whitespace-only input returns `"Uncategorized"`.

## Acceptance criteria

- Two articles on the same topic land in one section in the common case (case/whitespace,
  plural, acronym, single-typo variants all resolve to the existing label).
- Distinct topics are not over-merged (`"Art"` vs `"AI"` stay separate).
- Deterministic: the first matching existing label (by rule priority, then list order) wins.
