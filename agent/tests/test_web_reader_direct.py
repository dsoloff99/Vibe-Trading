"""Tests for the local ``direct`` backend of ``read_url``.

``VIBE_TRADING_WEB_READER=direct`` fetches the page from this machine and
extracts text locally instead of forwarding the URL to r.jina.ai.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.tools import web_reader_tool as wr


class _Resp:
    def __init__(self, body: bytes, url: str, status: int = 200, ctype: str = "text/html; charset=utf-8"):
        self._body = body
        self.url = url
        self.status_code = status
        self.headers = {"Content-Type": ctype}
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.raw = MagicMock()
        self.raw.read.side_effect = lambda n=-1, decode_content=True: body
        self.text = body.decode("utf-8", errors="replace")

    def close(self) -> None:  # pragma: no cover - trivial
        pass


@pytest.fixture
def direct_mode(monkeypatch):
    monkeypatch.setenv(wr._READER_MODE_ENV, "direct")
    monkeypatch.setattr(wr, "emit_progress", lambda *a, **k: None)


def test_default_mode_is_jina(monkeypatch):
    monkeypatch.delenv(wr._READER_MODE_ENV, raising=False)
    assert wr.reader_mode() == "jina"
    monkeypatch.setenv(wr._READER_MODE_ENV, "DIRECT")
    assert wr.reader_mode() == "direct"
    monkeypatch.setenv(wr._READER_MODE_ENV, "bogus")
    assert wr.reader_mode() == "jina"


def test_direct_mode_never_contacts_jina(direct_mode):
    html = b"<html><head><title>Hello &amp; Bye</title><script>x=1</script></head><body><h1>Head</h1><p>Body text</p></body></html>"
    with patch.object(wr.requests, "get", return_value=_Resp(html, "https://example.com/page")) as get:
        out = json.loads(wr.read_url("https://example.com/page"))
    called_url = get.call_args[0][0]
    assert not called_url.startswith(wr._JINA_PREFIX)
    assert called_url == "https://example.com/page"
    assert out["status"] == "ok"
    assert out["reader"] == "direct"
    assert out["title"] == "Hello & Bye"
    assert "Head" in out["content"] and "Body text" in out["content"]
    assert "x=1" not in out["content"]


def test_direct_mode_rejects_redirect_to_private_address(direct_mode):
    html = b"<html><body>internal</body></html>"
    with patch.object(wr.requests, "get", return_value=_Resp(html, "http://127.0.0.1:8899/settings")):
        out = json.loads(wr.read_url("https://example.com/bounce"))
    assert out["status"] == "error"
    assert "not allowed" in out["error"]


def test_direct_mode_surfaces_http_errors(direct_mode):
    with patch.object(wr.requests, "get", return_value=_Resp(b"nope", "https://example.com/x", status=503)):
        out = json.loads(wr.read_url("https://example.com/x"))
    assert out["status"] == "error"
    assert "503" in out["error"]


def test_direct_mode_plain_text_passthrough_and_truncation(direct_mode):
    body = ("word " * 5000).encode()
    with patch.object(wr.requests, "get", return_value=_Resp(body, "https://example.com/t.txt", ctype="text/plain")):
        out = json.loads(wr.read_url("https://example.com/t.txt"))
    assert out["status"] == "ok"
    assert out["length"] > wr._MAX_LENGTH
    assert "truncated" in out["content"]


def test_direct_mode_still_blocks_private_targets_up_front(direct_mode):
    with patch.object(wr.requests, "get") as get:
        out = json.loads(wr.read_url("http://192.168.1.10/admin"))
    assert out["status"] == "error"
    get.assert_not_called()
