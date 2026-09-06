"""Track what the advice would have done.

For each review we hold two books frozen at the review date: the actual
holdings and the hypothetical book after the recommended trades. Marking
both to market on the same closes, next to SPY, shows the value the advice
added or cost. Per-recommendation scoring compares each symbol's move since
the recommendation with SPY over the same window.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from src.advisor.pricing import PriceFetcher, fetch_close_panel, is_cash_like, latest_closes

_DIRECTION = {"buy": 1.0, "hold": 1.0, "sell": -1.0, "trim": -1.0}


def _book_from_snapshot(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a["id"]: {"cash_usd": float(a.get("cash_usd") or 0.0),
                      "positions": {p["symbol"]: float(p["quantity"]) for p in a["positions"]}}
            for a in snapshot["accounts"]}


def _asset_classes(snapshot: dict[str, Any]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for a in snapshot["accounts"]:
        for p in a["positions"]:
            out.setdefault(p["symbol"], p.get("asset_class"))
    return out


def _value_curve(book: dict[str, dict[str, Any]], closes: pd.DataFrame, classes: dict[str, str | None]) -> pd.Series:
    """Daily USD value of a frozen book. Symbols without prices are excluded
    consistently so both books stay comparable."""
    cash = sum(a["cash_usd"] for a in book.values())
    value = pd.Series(cash, index=closes.index, dtype="float64")
    for a in book.values():
        for sym, qty in a["positions"].items():
            if is_cash_like(sym, classes.get(sym)):
                value += qty
            elif sym in closes.columns:
                value += closes[sym] * qty
    return value


def score_recommendation(rec: dict[str, Any], price_now: float | None, spy_ret: float | None) -> dict[str, Any]:
    p0 = rec.get("price_at_rec")
    if p0 is None or price_now is None or spy_ret is None or rec["action"] not in _DIRECTION:
        return {"symbol_return": None, "benchmark_return": spy_ret, "excess": None, "hit": None}
    ret = price_now / p0 - 1.0
    excess = _DIRECTION[rec["action"]] * (ret - spy_ret)
    return {"symbol_return": round(ret, 4), "benchmark_return": round(spy_ret, 4),
            "excess": round(excess, 4), "hit": excess > 0}


def review_performance(review: dict[str, Any], snapshot: dict[str, Any], recs: list[dict[str, Any]],
                       today: date, fetcher: PriceFetcher | None = None) -> dict[str, Any]:
    benchmark = review.get("objectives", {}).get("benchmark", "SPY")
    start = date.fromisoformat(review["created_at"][:10])
    classes = _asset_classes(snapshot)
    symbols: dict[str, str | None] = dict(classes)
    for acct in review.get("hypothetical_book", {}).values():
        for sym in acct["positions"]:
            symbols.setdefault(sym, classes.get(sym))
    for r in recs:
        symbols.setdefault(r["symbol"], classes.get(r["symbol"]))
    symbols[benchmark] = "etf"

    closes, unresolved = fetch_close_panel(symbols, start, today, fetcher)
    closes = closes[closes.index >= pd.Timestamp(start)] if not closes.empty else closes
    if closes.empty or benchmark not in closes.columns:
        return {"review_id": review["id"], "since": start.isoformat(), "status": "no_data",
                "data_gaps": [f"{s}: no prices" for s in unresolved]}

    spy = closes[benchmark].dropna()
    actual = _value_curve(_book_from_snapshot(snapshot), closes, classes)
    hypo = _value_curve(review.get("hypothetical_book", {}), closes, classes)
    base = float(actual.iloc[0]) if len(actual) else 0.0
    bench_curve = base * spy / float(spy.iloc[0]) if len(spy) else spy

    now = latest_closes(closes)
    spy_ret = float(spy.iloc[-1] / spy.iloc[0] - 1.0) if len(spy) > 1 else None
    scored = [{**{k: r.get(k) for k in ("id", "symbol", "action", "status", "price_at_rec", "amount_usd", "confidence")},
               "price_now": now.get(r["symbol"]), **score_recommendation(r, now.get(r["symbol"]), spy_ret)}
              for r in recs]
    curve = [{"date": d.date().isoformat(), "actual": round(float(a), 2), "hypothetical": round(float(h), 2),
              "benchmark": round(float(b), 2) if pd.notna(b) else None}
             for d, a, h, b in zip(closes.index, actual, hypo, bench_curve.reindex(closes.index).ffill())]
    return {
        "review_id": review["id"], "since": start.isoformat(), "as_of": closes.index[-1].date().isoformat(),
        "status": "ok", "benchmark": benchmark, "benchmark_return": round(spy_ret, 4) if spy_ret is not None else None,
        "actual_value_start": round(base, 2), "actual_value_now": round(float(actual.iloc[-1]), 2),
        "hypothetical_value_now": round(float(hypo.iloc[-1]), 2),
        "advice_delta_usd": round(float(hypo.iloc[-1] - actual.iloc[-1]), 2),
        "actual_return": round(float(actual.iloc[-1] / base - 1.0), 4) if base else None,
        "hypothetical_return": round(float(hypo.iloc[-1] / base - 1.0), 4) if base else None,
        "curve": curve, "recommendations": scored,
        "data_gaps": [f"{s}: no prices" for s in unresolved],
    }


def scorecard(per_review: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for p in per_review if p.get("status") == "ok" for r in p["recommendations"] if r.get("hit") is not None]
    by_action: dict[str, dict[str, Any]] = {}
    for r in scored:
        b = by_action.setdefault(r["action"], {"n": 0, "hits": 0, "excess_sum": 0.0})
        b["n"] += 1; b["hits"] += int(r["hit"]); b["excess_sum"] += r["excess"]
    n = len(scored)
    return {
        "reviews": len(per_review), "scored_recommendations": n,
        "hit_rate": round(sum(int(r["hit"]) for r in scored) / n, 4) if n else None,
        "avg_excess_return": round(sum(r["excess"] for r in scored) / n, 4) if n else None,
        "by_action": {k: {"n": v["n"], "hit_rate": round(v["hits"] / v["n"], 4),
                          "avg_excess_return": round(v["excess_sum"] / v["n"], 4)} for k, v in by_action.items()},
        "advice_delta_usd_total": round(sum(p.get("advice_delta_usd", 0.0) for p in per_review if p.get("status") == "ok"), 2),
    }
