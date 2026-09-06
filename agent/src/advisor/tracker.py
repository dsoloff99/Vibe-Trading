"""Track what the advice would have done.

Each review freezes two books on its date: the actual holdings and the
advised book after the recommended trades. Marking both on the same daily
closes next to the benchmark shows the value the advice added or cost. Each
call is also scored on its own against the benchmark over the same window.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from src.advisor.evidence import asset_classes, book_from_snapshot
from src.advisor.pricing import is_cash_like, latest_closes

_DIRECTION = {"buy": 1.0, "hold": 1.0, "sell": -1.0, "trim": -1.0}
_SCORED_ACTIONS = ("buy", "sell", "trim")  # holds are reported but do not drive the hit rate


def _value_curve(book: dict[str, dict[str, Any]], closes: pd.DataFrame, classes: dict[str, str | None]) -> pd.Series:
    """Daily USD value of a frozen book. Symbols without prices are excluded
    consistently so both books stay comparable."""
    value = pd.Series(sum(a["cash_usd"] for a in book.values()), index=closes.index, dtype="float64")
    for a in book.values():
        for sym, qty in a["positions"].items():
            if is_cash_like(sym, classes.get(sym)):
                value += qty
            elif sym in closes.columns:
                value += closes[sym] * qty
    return value


def score_recommendation(rec: dict[str, Any], price_now: float | None, bench_ret: float | None) -> dict[str, Any]:
    p0 = rec.get("price_at_rec")
    if p0 is None or price_now is None or bench_ret is None or rec["action"] not in _DIRECTION:
        return {"symbol_return": None, "benchmark_return": bench_ret, "excess": None, "hit": None}
    ret = price_now / p0 - 1.0
    excess = _DIRECTION[rec["action"]] * (ret - bench_ret)
    return {"symbol_return": round(ret, 4), "benchmark_return": round(bench_ret, 4),
            "excess": round(excess, 4), "hit": excess > 0}


def review_performance(review: dict[str, Any], snapshot: dict[str, Any], recs: list[dict[str, Any]],
                       closes: pd.DataFrame, unresolved: list[str]) -> dict[str, Any]:
    """Mark one review's books on a close panel that starts at or before its date."""
    benchmark = review.get("objectives", {}).get("benchmark", "SPY")
    start = date.fromisoformat(review["created_at"][:10])
    classes = asset_classes(snapshot)
    gaps = [f"{s}: no prices" for s in unresolved]
    window = closes[closes.index >= pd.Timestamp(start)] if not closes.empty else closes
    if benchmark in window.columns:
        # The benchmark anchors day one. A symbol with no close on that day is
        # seeded with the price its recommendation was made at, so the advised
        # book starts at the same value as the actual book; any other gap is
        # carried at the nearest close so both books stay finite.
        window = window[window[benchmark].notna()].copy()
        if not window.empty:
            for r in recs:
                sym, p0 = r["symbol"], r.get("price_at_rec")
                if sym in window.columns and p0 and pd.isna(window[sym].iloc[0]):
                    window.iloc[0, window.columns.get_loc(sym)] = p0
        window = window.ffill().bfill()
    if window.empty or benchmark not in window.columns:
        return {"review_id": review["id"], "since": start.isoformat(), "status": "no_data", "data_gaps": gaps}

    bench = window[benchmark]
    actual = _value_curve(book_from_snapshot(snapshot), window, classes)
    advised = _value_curve(review.get("hypothetical_book", {}), window, classes)
    base = float(actual.iloc[0])
    if not base:
        return {"review_id": review["id"], "since": start.isoformat(), "status": "no_data", "data_gaps": gaps}
    bench_curve = base * bench / float(bench.iloc[0])
    bench_ret = float(bench.iloc[-1] / bench.iloc[0] - 1.0)

    now = latest_closes(window)
    scored = [{**{k: r.get(k) for k in ("id", "symbol", "action", "status", "price_at_rec", "amount_usd", "confidence")},
               "price_now": now.get(r["symbol"]), **score_recommendation(r, now.get(r["symbol"]), bench_ret)}
              for r in recs]
    curve = [{"date": d.date().isoformat(), "actual": round(float(a), 2), "hypothetical": round(float(h), 2),
              "benchmark": round(float(b), 2)}
             for d, a, h, b in zip(window.index, actual, advised, bench_curve)]
    return {
        "review_id": review["id"], "since": start.isoformat(), "as_of": window.index[-1].date().isoformat(),
        "status": "ok", "benchmark": benchmark, "benchmark_return": round(bench_ret, 4),
        "actual_value_start": round(base, 2), "actual_value_now": round(float(actual.iloc[-1]), 2),
        "hypothetical_value_now": round(float(advised.iloc[-1]), 2),
        "advice_delta_usd": round(float(advised.iloc[-1] - actual.iloc[-1]), 2),
        "actual_return": round(float(actual.iloc[-1] / base - 1.0), 4),
        "hypothetical_return": round(float(advised.iloc[-1] / base - 1.0), 4),
        "curve": curve, "recommendations": scored, "data_gaps": gaps,
    }


def scorecard(per_review: list[dict[str, Any]]) -> dict[str, Any]:
    all_scored = [r for p in per_review if p.get("status") == "ok" for r in p["recommendations"] if r.get("hit") is not None]
    by_action: dict[str, dict[str, Any]] = {}
    for r in all_scored:
        b = by_action.setdefault(r["action"], {"n": 0, "hits": 0, "excess_sum": 0.0})
        b["n"] += 1
        b["hits"] += int(r["hit"])
        b["excess_sum"] += r["excess"]
    scored = [r for r in all_scored if r["action"] in _SCORED_ACTIONS]
    n = len(scored)
    return {
        "reviews": len(per_review), "scored_recommendations": n,
        "hit_rate": round(sum(int(r["hit"]) for r in scored) / n, 4) if n else None,
        "avg_excess_return": round(sum(r["excess"] for r in scored) / n, 4) if n else None,
        "by_action": {k: {"n": v["n"], "hit_rate": round(v["hits"] / v["n"], 4),
                          "avg_excess_return": round(v["excess_sum"] / v["n"], 4)} for k, v in by_action.items()},
        "advice_delta_usd_total": round(sum(p.get("advice_delta_usd", 0.0) for p in per_review if p.get("status") == "ok"), 2),
    }
