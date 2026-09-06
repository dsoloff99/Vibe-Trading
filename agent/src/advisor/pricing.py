"""Price panels for the advisor, built on the project's market-data loaders.

The finance app sends plain symbols (``AAPL``, ``VTI``, ``BTC``). This module
maps them to loader spellings (``AAPL.US``, ``BTC-USDT``), fetches daily
closes, and hands back one wide DataFrame keyed by the app's own symbols so
the rest of the advisor never sees loader conventions.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Callable, Iterable

import pandas as pd

logger = logging.getLogger(__name__)

# Symbols the app may send without an asset class that are unambiguously crypto.
_KNOWN_CRYPTO = {
    "BTC", "ETH", "SOL", "DOGE", "ADA", "XRP", "LTC", "BCH", "AVAX", "DOT",
    "LINK", "MATIC", "UNI", "ATOM", "SHIB", "BNB", "TRX", "XLM", "ETC", "AAVE",
}
_STABLECOINS = {"USDC", "USDT", "DAI", "USD"}
_DATE_KEYS = ("date", "datetime", "trade_date", "time", "timestamp")

PriceFetcher = Callable[[list[str], str, str], dict[str, Any]]


def is_cash_like(symbol: str, asset_class: str | None) -> bool:
    return asset_class == "cash" or symbol.upper() in _STABLECOINS


def loader_symbol(symbol: str, asset_class: str | None = None) -> str:
    """Map an app symbol to the spelling the loader chain routes correctly."""
    s = symbol.strip().upper()
    if "." in s or "-" in s or "/" in s or s.startswith("^"):
        return s  # already suffixed (AAPL.US, BTC-USDT, EURUSD=X, ^SPX)
    if asset_class == "crypto" or (asset_class is None and s in _KNOWN_CRYPTO):
        return f"{s}-USDT"
    return f"{s}.US"


def _default_fetch(codes: list[str], start: str, end: str) -> dict[str, Any]:
    from src.market_data import fetch_market_data

    return fetch_market_data(
        codes=codes, start_date=start, end_date=end, source="auto",
        interval="1D", max_rows=100_000,
    )


def _records_to_series(records: Iterable[dict[str, Any]]) -> pd.Series:
    rows: dict[pd.Timestamp, float] = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        close = rec.get("close")
        stamp = next((rec[k] for k in _DATE_KEYS if k in rec), None)
        if close is None or stamp is None:
            continue
        try:
            ts = pd.Timestamp(stamp).normalize().tz_localize(None)
            rows[ts] = float(close)
        except (TypeError, ValueError):
            continue
    return pd.Series(rows, dtype="float64").sort_index()


def fetch_close_panel(
    symbols: dict[str, str | None],
    start: date,
    end: date,
    fetcher: PriceFetcher | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Return ``(closes, unresolved)``.

    ``symbols`` maps app symbol -> asset class (may be None). ``closes`` is a
    date-indexed DataFrame with one column per app symbol that resolved;
    ``unresolved`` lists the ones that did not. Cash-like symbols are never
    fetched. Loader failures for one symbol never fail the others.
    """
    fetch = fetcher or _default_fetch
    wanted = {s: loader_symbol(s, ac) for s, ac in symbols.items() if not is_cash_like(s, ac)}
    if not wanted:
        return pd.DataFrame(), []
    by_loader = {v: k for k, v in wanted.items()}
    try:
        raw = fetch(sorted(by_loader), start.isoformat(), end.isoformat())
    except Exception as exc:  # noqa: BLE001 - a loader outage is a data gap, not a crash
        logger.warning("advisor price fetch failed: %s", exc)
        raw = {}
    columns: dict[str, pd.Series] = {}
    for loader_sym, app_sym in by_loader.items():
        series = _records_to_series(raw.get(loader_sym) or [])
        if not series.empty:
            columns[app_sym] = series
    closes = pd.DataFrame(columns).sort_index() if columns else pd.DataFrame()
    closes = closes.ffill()
    unresolved = sorted(set(wanted) - set(closes.columns))
    return closes, unresolved


def lookback_start(end: date, days: int) -> date:
    return end - timedelta(days=days)


def latest_closes(closes: pd.DataFrame) -> dict[str, float]:
    if closes.empty:
        return {}
    last = closes.ffill().iloc[-1]
    return {str(k): float(v) for k, v in last.items() if pd.notna(v)}
