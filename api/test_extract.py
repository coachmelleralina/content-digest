"""Spec for feature 008 — extract.py: URL -> readable article text (issue #6).

Written before extract.py exists; the import below is the failing (red) assertion
that drives the implementation. No network: extract_article is pure, and the
fetch_html cases use httpx.MockTransport.
"""

from pathlib import Path

import httpx
import pytest

from extract import (
    EmptyExtractionError,
    ExtractedArticle,
    ExtractionError,
    FetchError,
    NotHtmlError,
    extract_article,
    fetch_html,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# --- extract_article (pure) -----------------------------------------------


def test_realistic_article_extracts_title_and_text() -> None:
    html = load_fixture("article.html")
    result = extract_article(html, "https://example.com/reading-habits")
    assert isinstance(result, ExtractedArticle)
    assert "Quiet Revolution in Reading Habits" in result.title
    assert "deliberate curation" in result.text
    assert "read-it-later tools" in result.text
    # Boilerplate must not leak into the article text.
    assert "All rights reserved" not in result.text


def test_nav_heavy_page_still_extracts_article_body() -> None:
    html = load_fixture("nav_heavy.html")
    result = extract_article(html, "https://portal.example.com/why-small-databases-win")
    assert "single Postgres instance" in result.text
    assert "operational surface small" in result.text
    # Nav/sidebar noise must not dominate.
    assert "which sandwich are you" not in result.text
    assert "Horoscopes" not in result.text


def test_junk_page_raises_empty_extraction_error() -> None:
    html = load_fixture("junk.html")
    with pytest.raises(EmptyExtractionError) as excinfo:
        extract_article(html, "https://example.com/paywalled")
    assert excinfo.value.message  # user-displayable, non-empty


def test_non_html_input_raises_not_html_error() -> None:
    with pytest.raises(NotHtmlError):
        extract_article('{"not": "html"}', "https://example.com/data.json")


def test_title_falls_back_to_title_tag() -> None:
    html = (
        "<html><head><title>Fallback Title From Tag</title></head><body><div>"
        "<p>Paragraph one has enough words to count as genuine readable article text "
        "for the extractor to keep, covering a plain topic in plain language.</p>"
        "<p>Paragraph two continues the thought with more sentences so that the "
        "extraction step does not classify the document as empty boilerplate.</p>"
        "<p>Paragraph three closes the short piece with a final remark, ensuring "
        "the body comfortably clears any minimum length heuristics.</p>"
        "</div></body></html>"
    )
    result = extract_article(html, "https://example.com/untitled")
    assert result.title == "Fallback Title From Tag"


def test_errors_share_base_and_message() -> None:
    for exc_type in (FetchError, NotHtmlError, EmptyExtractionError):
        assert issubclass(exc_type, ExtractionError)
    err = EmptyExtractionError()
    assert isinstance(err.message, str) and err.message
    assert str(err) == err.message


# --- fetch_html (httpx.MockTransport — no real network) --------------------


def _client_with(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler, follow_redirects=True)


def test_fetch_html_returns_body_for_html_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/html; charset=utf-8"}, text="<html>ok</html>"
        )

    transport = httpx.MockTransport(handler)
    assert fetch_html("https://example.com/a", transport=transport) == "<html>ok</html>"


def test_fetch_html_raises_fetch_error_on_non_200() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, headers={"content-type": "text/html"}, text="nope")

    with pytest.raises(FetchError):
        fetch_html("https://example.com/missing", transport=httpx.MockTransport(handler))


def test_fetch_html_raises_fetch_error_on_non_html_content_type() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF")

    with pytest.raises(FetchError):
        fetch_html("https://example.com/doc.pdf", transport=httpx.MockTransport(handler))


def test_fetch_html_raises_fetch_error_on_network_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(FetchError):
        fetch_html("https://unreachable.example", transport=httpx.MockTransport(handler))
