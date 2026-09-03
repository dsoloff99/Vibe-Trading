"""Web reader tool: fetch a URL as Markdown text via the Jina Reader API."""

from __future__ import annotations

import html as _html
import ipaddress
import json
import logging
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import requests

from src.agent.progress import emit_progress
from src.agent.tools import BaseTool
from src.security.scanner import with_security_warnings

logger = logging.getLogger(__name__)

_JINA_PREFIX = "https://r.jina.ai/"
_TIMEOUT = 30
_MAX_LENGTH = 8000
_CACHED_MARKER = "Warning: This is a cached snapshot"
# ``VIBE_TRADING_WEB_READER`` selects the backend: ``jina`` forwards every URL
# to the hosted r.jina.ai reader (best extraction, but the URL leaves this
# machine); ``direct`` fetches the page from here and extracts text locally.
_READER_MODE_ENV = "VIBE_TRADING_WEB_READER"
_DIRECT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 vibe-trading-reader"
)
_DIRECT_MAX_BYTES = 5 * 1024 * 1024


def reader_mode() -> str:
    """Return the configured backend, ``"jina"`` (default) or ``"direct"``."""
    mode = os.environ.get(_READER_MODE_ENV, "jina").strip().lower()
    return "direct" if mode == "direct" else "jina"


class _TextExtractor(HTMLParser):
    """Minimal HTML -> text extractor: drops script/style/nav noise, keeps the
    title and block structure so headings and paragraphs stay separated."""

    _SKIP = {"script", "style", "noscript", "template", "svg", "head"}
    _BLOCK = {
        "p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
        "section", "article", "header", "footer", "blockquote", "pre",
        "table", "ul", "ol", "hr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in self._BLOCK:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in self._BLOCK:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n\n", raw)
        return raw.strip()


def html_to_text(markup: str) -> tuple[str, str]:
    """Return ``(title, text)`` extracted from an HTML document."""
    parser = _TextExtractor()
    parser.feed(markup)
    parser.close()
    return _html.unescape(parser.title).strip(), parser.text()


def _read_url_direct(target_url: str) -> str:
    """Fetch ``target_url`` from this machine and extract its text locally.

    Redirect targets are re-checked against the same private-address guard as
    the original URL so a public host cannot bounce the reader onto a LAN or
    loopback address.
    """
    emit_progress(
        "fetching",
        message=f"GET {target_url[:60]}{'…' if len(target_url) > 60 else ''}",
    )
    resp = requests.get(
        target_url,
        headers={"User-Agent": _DIRECT_USER_AGENT, "Accept": "text/html,text/plain,*/*"},
        timeout=_TIMEOUT,
        allow_redirects=True,
        stream=True,
    )
    final_url = resp.url or target_url
    allowed, error = _url_allowed(final_url)
    if not allowed:
        resp.close()
        return json.dumps({"status": "error", "error": error}, ensure_ascii=False)
    if resp.status_code != 200:
        body = resp.text[:500]
        return json.dumps({
            "status": "error",
            "error": f"remote server returned HTTP {resp.status_code}: {body}",
        }, ensure_ascii=False)
    raw = resp.raw.read(_DIRECT_MAX_BYTES + 1, decode_content=True)
    encoding = resp.encoding or resp.apparent_encoding or "utf-8"
    body_text = raw[:_DIRECT_MAX_BYTES].decode(encoding, errors="replace")
    emit_progress("parsing", message="extracting text")
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "html" in content_type or body_text.lstrip()[:15].lower().startswith(("<!doctype", "<html")):
        title, text = html_to_text(body_text)
    else:
        title, text = "", body_text
    full_len = len(text)
    if full_len > _MAX_LENGTH:
        text = text[:_MAX_LENGTH] + f"\n\n... (truncated, total {full_len} chars)"
    result = {
        "status": "ok",
        "title": title,
        "url": final_url,
        "content": text,
        "length": full_len,
        "reader": "direct",
    }
    result = with_security_warnings(result, fields=("content",))
    return json.dumps(result, ensure_ascii=False)


def _url_allowed(url: str) -> tuple[bool, str]:
    """Return whether a URL is safe to forward to the remote reader service."""
    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return False, "target URL is not allowed"

    if parsed.scheme.lower() not in {"http", "https"}:
        return False, "target URL is not allowed"
    if not parsed.hostname:
        return False, "target URL is not allowed"
    if parsed.username or parsed.password:
        return False, "target URL is not allowed"

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        return False, "target URL is not allowed"

    ip_host = host.split("%", 1)[0]
    try:
        ip = ipaddress.ip_address(ip_host)
    except ValueError:
        return True, ""

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or not ip.is_global
    ):
        return False, "target URL is not allowed"
    return True, ""


def read_url(url: str, no_cache: bool = False) -> str:
    """Fetch web page content via the Jina Reader API.

    The full URL (including query string) is sent to the third-party Jina
    Reader service (r.jina.ai); never pass credentials/tokens or private
    addresses. Results may be a cached snapshot.

    Args:
        url: Target URL.
        no_cache: When true, ask the reader for a fresh (uncached) fetch.

    Returns:
        JSON result with title, content, url; ``cached: true`` is added
        when the reader served a stale snapshot.
    """
    target_url = url.strip()
    allowed, error = _url_allowed(target_url)
    if not allowed:
        return json.dumps({"status": "error", "error": error}, ensure_ascii=False)

    if reader_mode() == "direct":
        try:
            return _read_url_direct(target_url)
        except requests.Timeout:
            return json.dumps({"status": "error", "error": f"Request timed out ({_TIMEOUT}s)"}, ensure_ascii=False)
        except Exception as exc:
            logger.warning("read_url direct fetch failed: %s", exc)
            return json.dumps(
                {"status": "error", "error": f"direct fetch failed: {exc}"},
                ensure_ascii=False,
            )

    try:
        headers = {"Accept": "text/markdown"}
        if no_cache:
            headers["x-no-cache"] = "true"
        emit_progress(
            "fetching",
            message=f"GET {target_url[:60]}{'…' if len(target_url) > 60 else ''}",
        )
        resp = requests.get(
            f"{_JINA_PREFIX}{target_url}",
            headers=headers,
            timeout=_TIMEOUT,
        )
        emit_progress("parsing", message="extracting markdown")
        if resp.status_code != 200:
            logger.warning("read_url upstream HTTP %s: %s", resp.status_code, resp.text[:500])
            return json.dumps({
                "status": "error",
                "error": f"remote reader returned HTTP {resp.status_code}: {resp.text[:500]}",
            }, ensure_ascii=False)

        text = resp.text
        title = ""
        for line in text.split("\n"):
            if line.startswith("Title:"):
                title = line[6:].strip()
                break

        if len(text) > _MAX_LENGTH:
            text = text[:_MAX_LENGTH] + f"\n\n... (truncated, total {len(resp.text)} chars)"

        result = {
            "status": "ok",
            "title": title,
            "url": target_url,
            "content": text,
            "length": len(resp.text),
        }
        if _CACHED_MARKER in resp.text:
            result["cached"] = True
        result = with_security_warnings(result, fields=("content",))
        return json.dumps(result, ensure_ascii=False)

    except requests.Timeout:
        return json.dumps({"status": "error", "error": f"Request timed out ({_TIMEOUT}s)"}, ensure_ascii=False)
    except Exception as exc:
        logger.warning("read_url request failed: %s", exc)
        return json.dumps(
            {"status": "error", "error": f"remote reader request failed: {exc}"},
            ensure_ascii=False,
        )


class WebReaderTool(BaseTool):
    """Web reader tool."""

    name = "read_url"
    description = "Fetch web page content: provide a URL and receive the page as Markdown text. Useful for reading docs, articles, API references, etc."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL of the web page to read"},
            "no_cache": {"type": "boolean", "description": "Request a fresh (uncached) fetch", "default": False},
        },
        "required": ["url"],
    }
    repeatable = True

    def execute(self, **kwargs) -> str:
        """Fetch web page."""
        return read_url(kwargs["url"], no_cache=bool(kwargs.get("no_cache", False)))
