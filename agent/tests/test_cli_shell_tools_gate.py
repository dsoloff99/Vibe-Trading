"""The interactive CLI must not register shell tools unless the operator opts
in with ``VIBE_TRADING_ENABLE_SHELL_TOOLS`` — the same gate the API, MCP and
IM channel surfaces already honour."""
from __future__ import annotations

from src.config.accessor import reset_env_config

from cli._legacy import _cli_shell_tools_enabled


def test_cli_shell_tools_off_by_default(monkeypatch):
    monkeypatch.delenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", raising=False)
    reset_env_config()
    assert _cli_shell_tools_enabled() is False


def test_cli_shell_tools_env_opt_in(monkeypatch):
    monkeypatch.setenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", "1")
    reset_env_config()
    assert _cli_shell_tools_enabled() is True


def test_cli_shell_tools_explicit_off(monkeypatch):
    monkeypatch.setenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", "0")
    reset_env_config()
    assert _cli_shell_tools_enabled() is False
