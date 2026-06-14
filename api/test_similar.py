"""Spec for feature 019 — similar.py: AI ranks board cards by meaning.

No network: httpx.Client(MockTransport) is injected via the client= kwarg.
"""

from __future__ import annotations

import json

import httpx
import pytest

from similar import (
    SimilarApiError,
    SimilarConfigError,
    SimilarParseError,
    SimilarRef,
    build_similar_prompt,
    find_similar,
)

TARGET = {
    "id": "t-0",
    "title": "Deep work and focus",
    "summary": "How to concentrate without distractions.",
    "tags": ["productivity", "focus"],
    "language": "uk",
}
OTHERS = [
    {"id": "c-1", "title": "Time blocking", "summary": "Plan your day in blocks.",
     "tags": ["productivity"]},
    {"id": "c-2", "title": "Sleep science", "summary": "Why rest matters.", "tags": ["health"]},
    {"id": "c-3", "title": "Pomodoro", "summary": "Work in 25-min sprints.",
     "tags": ["productivity", "focus"]},
    {"id": "c-4", "title": "Cooking pasta", "summary": "Boil water, add salt.", "tags": ["food"]},
]


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _ok(body: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        content = json.dumps(body)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    return handler


# --- no-AI fast path ----------------------------------------------------------


def test_no_others_returns_empty_without_calling_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["n"] += 1
        return httpx.Response(200, json={})

    assert find_similar(TARGET, [], client=_client(handler)) == []
    assert called["n"] == 0


# --- happy path ---------------------------------------------------------------


def test_returns_validated_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    body = {"similar": [{"id": "c-3", "reason": "Both about focus"},
                        {"id": "c-1", "reason": "Both productivity"}]}
    refs = find_similar(TARGET, OTHERS, client=_client(_ok(body)))
    assert refs == [SimilarRef(id="c-3", reason="Both about focus"),
                    SimilarRef(id="c-1", reason="Both productivity")]


def test_filters_out_ids_not_on_the_board(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    body = {"similar": [{"id": "c-1", "reason": "ok"},
                        {"id": "ghost", "reason": "hallucinated id"}]}
    refs = find_similar(TARGET, OTHERS, client=_client(_ok(body)))
    assert [r.id for r in refs] == ["c-1"]


def test_dedupes_and_caps_at_three(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    body = {"similar": [
        {"id": "c-1", "reason": "a"}, {"id": "c-1", "reason": "dup"},
        {"id": "c-2", "reason": "b"}, {"id": "c-3", "reason": "c"},
        {"id": "c-4", "reason": "d"},
    ]}
    refs = find_similar(TARGET, OTHERS, client=_client(_ok(body)))
    assert [r.id for r in refs] == ["c-1", "c-2", "c-3"]


def test_empty_similar_array_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    assert find_similar(TARGET, OTHERS, client=_client(_ok({"similar": []}))) == []


def test_tolerates_markdown_code_fences(monkeypatch: pytest.MonkeyPatch) -> None:
    """Models (e.g. haiku-4.5) wrap JSON in ```json fences — found live in prod."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    fenced = '```json\n{"similar": [{"id": "c-1", "reason": "related"}]}\n```'

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": fenced}}]})

    refs = find_similar(TARGET, OTHERS, client=_client(handler))
    assert [r.id for r in refs] == ["c-1"]


def test_tolerates_trailing_prose_after_fence(monkeypatch: pytest.MonkeyPatch) -> None:
    """haiku-4.5 appends an explanation AFTER the ```json fence — found live in prod."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    content = (
        '```json\n{\n  "similar": [{"id": "c-1", "reason": "ok"}]\n}\n```\n\n'
        "These two cards share the productivity theme, so they are related."
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    refs = find_similar(TARGET, OTHERS, client=_client(handler))
    assert [r.id for r in refs] == ["c-1"]


# --- prompt -------------------------------------------------------------------


def test_prompt_names_the_language_and_candidate_ids() -> None:
    system, user = build_similar_prompt(TARGET, OTHERS, "uk")
    assert "Ukrainian" in system
    assert "c-1" in user and "c-4" in user
    assert TARGET["title"] in user


def test_unsupported_language_raises_value_error() -> None:
    with pytest.raises(ValueError):
        build_similar_prompt(TARGET, OTHERS, "fr")


# --- error mapping ------------------------------------------------------------


def test_missing_key_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SimilarConfigError):
        find_similar(TARGET, OTHERS, client=_client(_ok({"similar": []})))


def test_http_500_raises_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(SimilarApiError):
        find_similar(TARGET, OTHERS, client=_client(handler))


def test_malformed_json_raises_parse_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})

    with pytest.raises(SimilarParseError):
        find_similar(TARGET, OTHERS, client=_client(handler))
