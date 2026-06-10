"""Spec for feature 009 — digest module (issue #7).

Written before digest.py exists; the import below is the failing (red) assertion
that drives the implementation. All HTTP traffic goes through httpx.MockTransport —
no real OpenRouter calls (the live smoke test is issue #8).
"""

import json

import httpx
import pytest
from pydantic import ValidationError

from digest import (
    DEFAULT_MODEL,
    MAX_INPUT_CHARS,
    OPENROUTER_URL,
    Digest,
    DigestApiError,
    DigestConfigError,
    DigestParseError,
    build_user_prompt,
    digest_text,
    truncate_text,
)

VALID_PAYLOAD = {
    "summary": "A short summary of the article.",
    "key_points": ["First point", "Second point"],
    "tags": ["ai", "testing"],
    "category": "Technology",
}


def completion_response(content: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        json={"choices": [{"message": {"content": content}}]},
    )


def mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def _api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)


# --- happy path -----------------------------------------------------------


def test_happy_path_valid_json_returns_digest() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return completion_response(json.dumps(VALID_PAYLOAD))

    result = digest_text("Some article text.", title="A title", client=mock_client(handler))

    assert isinstance(result, Digest)
    assert result.summary == VALID_PAYLOAD["summary"]
    assert result.key_points == VALID_PAYLOAD["key_points"]
    assert result.tags == VALID_PAYLOAD["tags"]
    assert result.category == VALID_PAYLOAD["category"]
    # exactly ONE chat-completion call, to the right URL, with auth + default model
    assert len(requests) == 1
    assert str(requests[0].url) == OPENROUTER_URL
    assert requests[0].headers["Authorization"] == "Bearer test-key"
    assert json.loads(requests[0].content)["model"] == DEFAULT_MODEL


def test_model_overridable_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "some/other-model")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return completion_response(json.dumps(VALID_PAYLOAD))

    digest_text("text", client=mock_client(handler))
    assert json.loads(requests[0].content)["model"] == "some/other-model"


def test_code_fenced_json_is_parsed() -> None:
    fenced = "```json\n" + json.dumps(VALID_PAYLOAD) + "\n```"

    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response(fenced)

    result = digest_text("text", client=mock_client(handler))
    assert result.summary == VALID_PAYLOAD["summary"]


# --- parse failures -------------------------------------------------------


def test_malformed_json_raises_parse_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response("Sorry, I cannot produce JSON today.")

    with pytest.raises(DigestParseError) as exc_info:
        digest_text("text", client=mock_client(handler))
    assert str(exc_info.value)  # user-displayable message


def test_schema_invalid_output_raises_parse_error() -> None:
    bad = dict(VALID_PAYLOAD, key_points=[])  # violates 1..8

    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response(json.dumps(bad))

    with pytest.raises(DigestParseError):
        digest_text("text", client=mock_client(handler))


def test_missing_choices_raises_parse_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    with pytest.raises(DigestParseError):
        digest_text("text", client=mock_client(handler))


# --- API / config failures ------------------------------------------------


def test_http_500_raises_api_error_with_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "upstream exploded"})

    with pytest.raises(DigestApiError) as exc_info:
        digest_text("text", client=mock_client(handler))
    assert exc_info.value.status == 500
    assert str(exc_info.value)


def test_network_failure_raises_api_error_without_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(DigestApiError) as exc_info:
        digest_text("text", client=mock_client(handler))
    assert exc_info.value.status is None


def test_missing_api_key_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:  # must never be reached
        raise AssertionError("HTTP call attempted without an API key")

    with pytest.raises(DigestConfigError) as exc_info:
        digest_text("text", client=mock_client(handler))
    assert "OPENROUTER_API_KEY" in str(exc_info.value)


def test_empty_api_key_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "   ")
    with pytest.raises(DigestConfigError):
        digest_text("text", client=mock_client(lambda r: completion_response("{}")))


# --- Digest model validation ----------------------------------------------


def test_digest_rejects_empty_summary() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="   ", key_points=["a"], tags=["t"], category="Tech")


def test_digest_rejects_zero_key_points() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="s", key_points=[], tags=["t"], category="Tech")


def test_digest_rejects_nine_key_points() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="s", key_points=[f"p{i}" for i in range(9)], tags=["t"], category="Tech")


def test_digest_rejects_seven_tags() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="s", key_points=["a"], tags=[f"t{i}" for i in range(7)], category="Tech")


def test_digest_rejects_multiline_category() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="s", key_points=["a"], tags=["t"], category="Tech\nNews")


def test_digest_accepts_bounds() -> None:
    d = Digest(
        summary="s",
        key_points=[f"p{i}" for i in range(8)],
        tags=[f"t{i}" for i in range(6)],
        category="Free-form AI label",
    )
    assert len(d.key_points) == 8 and len(d.tags) == 6


# --- prompt builder / truncation -------------------------------------------


def test_truncate_text_caps_at_limit() -> None:
    long_text = "x" * (MAX_INPUT_CHARS + 5000)
    assert len(truncate_text(long_text)) == MAX_INPUT_CHARS
    assert truncate_text("short") == "short"


def test_user_prompt_truncates_long_input_and_includes_title() -> None:
    long_text = "y" * (MAX_INPUT_CHARS * 2)
    prompt = build_user_prompt(long_text, title="My Title")
    assert "My Title" in prompt
    assert "y" * MAX_INPUT_CHARS in prompt
    assert "y" * (MAX_INPUT_CHARS + 1) not in prompt
