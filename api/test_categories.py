"""Spec for feature 020 — resolve_category, Python port of app/src/lib/categories.ts.

Mirrors every case in app/src/lib/categories.spec.ts so the two implementations
stay in sync (feature-002 defines the rules; feature-020 ports them to the save path).
"""

from __future__ import annotations

from categories import resolve_category


def test_returns_trimmed_raw_label_when_no_existing_match() -> None:
    assert resolve_category("  Web3 ", []) == "Web3"


def test_collapses_inner_whitespace_in_new_label() -> None:
    assert resolve_category("Machine  Learning", []) == "Machine Learning"


def test_matches_existing_case_insensitively_and_returns_existing_casing() -> None:
    assert resolve_category(" machine learning ", ["Machine Learning"]) == "Machine Learning"


def test_treats_hyphens_as_spaces_when_matching() -> None:
    assert resolve_category("Machine-Learning", ["Machine Learning"]) == "Machine Learning"


def test_merges_singular_plural_variants() -> None:
    assert resolve_category("Startups", ["Startup"]) == "Startup"
    assert resolve_category("Startup", ["Startups"]) == "Startups"


def test_matches_acronym_to_spelled_out_existing_label() -> None:
    assert resolve_category("AI", ["Artificial Intelligence"]) == "Artificial Intelligence"


def test_matches_spelled_out_label_to_existing_acronym() -> None:
    assert resolve_category("Artificial Intelligence", ["AI"]) == "AI"


def test_tolerates_single_typo_in_longer_labels() -> None:
    assert (
        resolve_category("Artifical Intelligence", ["Artificial Intelligence"])
        == "Artificial Intelligence"
    )


def test_does_not_over_merge_short_distinct_labels() -> None:
    assert resolve_category("Art", ["AI"]) == "Art"


def test_does_not_merge_unrelated_topics() -> None:
    assert resolve_category("Health", ["Crypto", "AI"]) == "Health"


def test_prefers_exact_fold_match_over_weaker_rules_and_earlier_entries() -> None:
    assert resolve_category("ai", ["Artificial Intelligence", "AI"]) == "AI"


def test_empty_or_whitespace_only_input_returns_uncategorized() -> None:
    assert resolve_category("   ", ["AI"]) == "Uncategorized"
