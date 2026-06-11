"""Spec for feature 009 (issue #7) + feature 014 (issue #13) — digest module.

Feature 014 reworks the digest: ELI5 explanation, key_points become grounded
{takeaway, quote} objects with code-side quote verification, canonical tags with
code-side normalization, and a language parameter (uk/ru/en). All HTTP traffic
goes through httpx.MockTransport — no real OpenRouter calls.
"""

import json

import httpx
import pytest
from pydantic import ValidationError

from digest import (
    ALLOWED_LANGUAGES,
    DEFAULT_MODEL,
    MAX_INPUT_CHARS,
    OPENROUTER_URL,
    Digest,
    DigestApiError,
    DigestConfigError,
    DigestParseError,
    KeyPoint,
    build_system_prompt,
    build_user_prompt,
    digest_text,
    normalize_tags,
    truncate_text,
    verify_quotes,
)

SOURCE_TEXT = (
    "Readability is the ease with which a reader can understand a written text. "
    "The concept exists in both natural language and programming languages. "
    "Higher readability eases reading effort and speed for any reader."
)

VALID_PAYLOAD = {
    "summary": "Це проста стаття про те, як легко читати тексти.",
    "key_points": [
        {
            "takeaway": "Прості тексти читати легше.",
            "quote": "Readability is the ease",
        },
        {
            "takeaway": "Це стосується і коду.",
            "quote": "natural language and programming languages",
        },
        {
            "takeaway": "Читабельність економить зусилля.",
            "quote": "eases reading effort and speed",
        },
    ],
    "tags": ["читання", "тексти"],
    "category": "Technology",
}


def kp(takeaway: str = "a thought", quote: str | None = None) -> KeyPoint:
    return KeyPoint(takeaway=takeaway, quote=quote)


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

    result = digest_text(SOURCE_TEXT, title="A title", client=mock_client(handler))

    assert isinstance(result, Digest)
    assert result.summary == VALID_PAYLOAD["summary"]
    assert [p.takeaway for p in result.key_points] == [
        p["takeaway"] for p in VALID_PAYLOAD["key_points"]
    ]
    # all three quotes occur verbatim in SOURCE_TEXT → all survive verification
    assert [p.quote for p in result.key_points] == [
        p["quote"] for p in VALID_PAYLOAD["key_points"]
    ]
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

    digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert json.loads(requests[0].content)["model"] == "some/other-model"


def test_code_fenced_json_is_parsed() -> None:
    fenced = "```json\n" + json.dumps(VALID_PAYLOAD) + "\n```"

    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response(fenced)

    result = digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert result.summary == VALID_PAYLOAD["summary"]


# --- system prompt (feature 014: ELI5 + language + exact quotes + canonical tags)


def test_system_prompt_contains_eli5_instruction() -> None:
    prompt = build_system_prompt("uk")
    assert "child" in prompt.lower()  # explain like to a child
    assert "jargon" in prompt.lower()  # no jargon; terms explained in brackets
    assert "brackets" in prompt.lower()


def test_system_prompt_contains_exact_quote_instruction() -> None:
    prompt = build_system_prompt("uk")
    assert "EXACTLY" in prompt
    assert "character for character" in prompt
    assert "12 words" in prompt
    assert "original language" in prompt.lower()


def test_system_prompt_contains_canonical_tag_instruction() -> None:
    prompt = build_system_prompt("uk")
    assert "canonical" in prompt.lower()
    assert "lowercase" in prompt.lower()
    assert "reused across" in prompt.lower()


@pytest.mark.parametrize(
    ("language", "name"),
    [("uk", "Ukrainian"), ("ru", "Russian"), ("en", "English")],
)
def test_system_prompt_names_target_language(language: str, name: str) -> None:
    assert name in build_system_prompt(language)


def test_system_prompt_rejects_unknown_language() -> None:
    with pytest.raises(ValueError):
        build_system_prompt("de")


def test_digest_text_sends_language_specific_system_prompt() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return completion_response(json.dumps(VALID_PAYLOAD))

    digest_text(SOURCE_TEXT, client=mock_client(handler), language="en")
    messages = json.loads(requests[0].content)["messages"]
    assert messages[0]["role"] == "system"
    assert "English" in messages[0]["content"]


def test_digest_text_rejects_unknown_language_before_http() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # must never be reached
        raise AssertionError("HTTP call attempted with an invalid language")

    with pytest.raises(ValueError):
        digest_text(SOURCE_TEXT, client=mock_client(handler), language="fr")


def test_payload_requests_lowest_latency_provider(monkeypatch) -> None:
    """OpenRouter from Vercel routed to slow providers (177s vs 8s local, found
    live) — the payload must pin provider sorting to latency."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    seen = {}

    def handler(request):
        import json as _json
        seen.update(_json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": _json.dumps(VALID_PAYLOAD)}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    digest_text("some text", client=client)
    assert seen.get("provider") == {"sort": "latency"}


def test_allowed_languages_constant() -> None:
    assert set(ALLOWED_LANGUAGES) == {"uk", "ru", "en"}


# --- quote verification (feature 014) ---------------------------------------


def test_verify_quotes_keeps_quote_found_in_source() -> None:
    points = [kp(quote="ease with which a reader")]
    verified = verify_quotes(points, SOURCE_TEXT)
    assert verified[0].quote == "ease with which a reader"
    assert verified[0].takeaway == points[0].takeaway


def test_verify_quotes_nulls_quote_not_in_source() -> None:
    points = [kp(takeaway="kept thought", quote="this fragment was hallucinated")]
    verified = verify_quotes(points, SOURCE_TEXT)
    assert verified[0].quote is None
    assert verified[0].takeaway == "kept thought"  # takeaway survives


def test_verify_quotes_is_whitespace_normalized() -> None:
    source = "First line ends here\nand   continues\twith spacing."
    points = [kp(quote="ends here and continues with")]
    assert verify_quotes(points, source)[0].quote == "ends here and continues with"


def test_verify_quotes_passes_none_through() -> None:
    points = [kp(quote=None)]
    assert verify_quotes(points, SOURCE_TEXT)[0].quote is None


def test_verify_quotes_strips_leading_list_markers() -> None:
    """Extracted text carries '- ' / '* ' / '\u2022 ' bullet markup that the rendered
    page does not show — keep the quote but without the marker, so the
    text-fragment deep link can actually match the DOM (issue found live)."""
    source = "Intro.\n- Assign roles to define what actions are allowed.\nMore."
    points = [kp(quote="- Assign roles to define what actions")]
    verified = verify_quotes(points, source)
    assert verified[0].quote == "Assign roles to define what actions"


def test_verify_quotes_strips_markers_before_matching() -> None:
    # Marker stripped -> the remaining text must still be verified in source.
    points = [kp(quote="\u2022 totally hallucinated bullet")]
    assert verify_quotes(points, SOURCE_TEXT)[0].quote is None


def test_digest_text_nulls_hallucinated_quotes() -> None:
    payload = dict(
        VALID_PAYLOAD,
        key_points=[
            {"takeaway": "real", "quote": "ease with which a reader"},
            {"takeaway": "fake", "quote": "completely invented words here"},
        ],
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response(json.dumps(payload))

    result = digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert result.key_points[0].quote == "ease with which a reader"
    assert result.key_points[1].quote is None
    assert result.key_points[1].takeaway == "fake"


# --- tag normalization (feature 014) -----------------------------------------


def test_normalize_tags_lowercases() -> None:
    assert normalize_tags(["AI", "Продуктивність"]) == ["ai", "продуктивність"]


def test_normalize_tags_truncates_list_to_four() -> None:
    assert normalize_tags(["a", "b", "c", "d", "e", "f"]) == ["a", "b", "c", "d"]


def test_normalize_tags_truncates_long_tag_to_24_chars() -> None:
    long_tag = "x" * 30
    assert normalize_tags([long_tag]) == ["x" * 24]


def test_normalize_tags_strips_and_drops_empty() -> None:
    assert normalize_tags(["  ai  ", "   ", "health"]) == ["ai", "health"]


def test_digest_normalizes_tags_via_model() -> None:
    payload = dict(VALID_PAYLOAD, tags=["AI", "Health", "Tech", "Work", "Extra"])

    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response(json.dumps(payload))

    result = digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert result.tags == ["ai", "health", "tech", "work"]  # lowered + capped at 4


# --- parse failures -------------------------------------------------------


def test_malformed_json_raises_parse_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response("Sorry, I cannot produce JSON today.")

    with pytest.raises(DigestParseError) as exc_info:
        digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert str(exc_info.value)  # user-displayable message


def test_schema_invalid_output_raises_parse_error() -> None:
    bad = dict(VALID_PAYLOAD, key_points=[])  # violates 1..8

    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response(json.dumps(bad))

    with pytest.raises(DigestParseError):
        digest_text(SOURCE_TEXT, client=mock_client(handler))


def test_old_string_key_points_raise_parse_error() -> None:
    # the pre-014 shape (list of strings) no longer validates
    bad = dict(VALID_PAYLOAD, key_points=["plain string point"])

    def handler(request: httpx.Request) -> httpx.Response:
        return completion_response(json.dumps(bad))

    with pytest.raises(DigestParseError):
        digest_text(SOURCE_TEXT, client=mock_client(handler))


def test_missing_choices_raises_parse_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    with pytest.raises(DigestParseError):
        digest_text(SOURCE_TEXT, client=mock_client(handler))


# --- API / config failures ------------------------------------------------


def test_http_500_raises_api_error_with_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "upstream exploded"})

    with pytest.raises(DigestApiError) as exc_info:
        digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert exc_info.value.status == 500
    assert str(exc_info.value)


def test_network_failure_raises_api_error_without_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(DigestApiError) as exc_info:
        digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert exc_info.value.status is None


def test_missing_api_key_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:  # must never be reached
        raise AssertionError("HTTP call attempted without an API key")

    with pytest.raises(DigestConfigError) as exc_info:
        digest_text(SOURCE_TEXT, client=mock_client(handler))
    assert "OPENROUTER_API_KEY" in str(exc_info.value)


def test_empty_api_key_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "   ")
    with pytest.raises(DigestConfigError):
        digest_text(SOURCE_TEXT, client=mock_client(lambda r: completion_response("{}")))


# --- KeyPoint / Digest model validation -------------------------------------


def test_key_point_rejects_empty_takeaway() -> None:
    with pytest.raises(ValidationError):
        KeyPoint(takeaway="   ", quote=None)


def test_key_point_quote_optional() -> None:
    assert KeyPoint(takeaway="t", quote=None).quote is None
    assert KeyPoint(takeaway="t", quote="q").quote == "q"


def test_digest_rejects_empty_summary() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="   ", key_points=[kp()], tags=["t"], category="Tech")


def test_digest_rejects_zero_key_points() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="s", key_points=[], tags=["t"], category="Tech")


def test_digest_rejects_nine_key_points() -> None:
    with pytest.raises(ValidationError):
        Digest(
            summary="s",
            key_points=[kp(f"p{i}") for i in range(9)],
            tags=["t"],
            category="Tech",
        )


def test_digest_rejects_multiline_category() -> None:
    with pytest.raises(ValidationError):
        Digest(summary="s", key_points=[kp()], tags=["t"], category="Tech\nNews")


def test_digest_accepts_bounds() -> None:
    d = Digest(
        summary="s",
        key_points=[kp(f"p{i}") for i in range(8)],
        tags=[f"t{i}" for i in range(6)],  # normalized down to 4, not rejected
        category="Free-form AI label",
    )
    assert len(d.key_points) == 8 and len(d.tags) == 4


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
