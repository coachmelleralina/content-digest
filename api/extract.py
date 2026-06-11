"""Feature 008 — URL -> readable article text (issue #6).

Pure extraction core (`extract_article`) built on trafilatura, a thin httpx
fetcher (`fetch_html`), and a composition (`extract_from_url`). Typed errors all
derive from ExtractionError and carry a user-displayable `message`, so the API
layer (issue #8) can always render a clear error — never a blank/broken card.
"""

from __future__ import annotations

import html as html_module
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import trafilatura

# Below this many characters of extracted text we treat the page as empty
# (paywall shells, "subscribe to continue" stubs, nav-only pages).
MIN_TEXT_CHARS = 120

_HTML_TAG_RE = re.compile(
    r"<\s*(?:!doctype|html|head|body|article|main|div|section|p|h[1-6]|title|meta|a)\b",
    re.IGNORECASE,
)
_TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


class ExtractionError(Exception):
    """Base error; `message` is safe to display to the user."""

    default_message = "Could not extract an article from that link."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class FetchError(ExtractionError):
    """URL unreachable, timed out, non-2xx, or not an HTML page."""

    default_message = (
        "Could not fetch that URL — the site may be down, blocking requests, "
        "or not serving a web page."
    )


class NotHtmlError(ExtractionError):
    """The payload is not HTML (JSON, PDF bytes, plain junk, ...)."""

    default_message = "That link does not point to a readable web page."


class EmptyExtractionError(ExtractionError):
    """HTML parsed but no usable article text (paywall / empty page)."""

    default_message = (
        "No readable article text was found on that page — it may be paywalled or empty."
    )


@dataclass(frozen=True)
class ExtractedArticle:
    title: str
    text: str


def _looks_like_html(payload: str) -> bool:
    return bool(payload) and _HTML_TAG_RE.search(payload) is not None


def _title_from_title_tag(html: str) -> str | None:
    match = _TITLE_TAG_RE.search(html)
    if not match:
        return None
    title = html_module.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title or None


def extract_article(html: str, url: str) -> ExtractedArticle:
    """Pure: HTML string + source URL -> ExtractedArticle. No network."""
    if not _looks_like_html(html):
        raise NotHtmlError()

    text = trafilatura.extract(html, url=url, include_comments=False)
    if text is None or len(text.strip()) < MIN_TEXT_CHARS:
        raise EmptyExtractionError()

    title: str | None = None
    metadata = trafilatura.extract_metadata(html, default_url=url)
    if metadata is not None and metadata.title:
        title = metadata.title.strip() or None
    if title is None:
        title = _title_from_title_tag(html)  # fallback: raw <title> tag
    if title is None:
        title = urlparse(url).netloc or url  # last resort: never an empty title

    return ExtractedArticle(title=title, text=text.strip())


def fetch_html(
    url: str,
    timeout: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> str:
    """GET the URL (following redirects) and return the HTML body.

    `transport` exists for tests (httpx.MockTransport) — never pass it in
    production code. Raises FetchError on network errors, timeouts, non-2xx
    responses, or non-HTML content types.
    """
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            transport=transport,
            # Several sites (e.g. Wikipedia) reject httpx's default UA with 403.
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36 content-digest/0.1"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        ) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        raise FetchError() from exc

    if response.status_code < 200 or response.status_code >= 300:
        raise FetchError(
            f"The page could not be fetched (HTTP {response.status_code})."
        )

    content_type = response.headers.get("content-type", "").lower()
    if not any(content_type.startswith(html_type) for html_type in _HTML_CONTENT_TYPES):
        raise FetchError("That link returned something other than a web page.")

    return response.text


def extract_from_url(url: str, timeout: float = 10.0) -> ExtractedArticle:
    """Compose fetch_html + extract_article. Raises ExtractionError subclasses."""
    return extract_article(fetch_html(url, timeout=timeout), url)
