"""Deterministic evidence for a review: valuation, weights, risk, benchmark.

Everything here is computed from the pushed holdings and a close panel. The
LLM only ever sees these numbers; it never sources a price itself.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

import pandas as pd

from src.advisor.pricing import infer_asset_class, is_cash_like, latest_closes

LOOKBACK_DAYS = 365


def book_from_snapshot(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Per-account cash and positions, the shape both the advised book and the
    tracker work on."""
    return {
        a["id"]: {"type": a.get("type", "taxable"), "cash_usd": float(a.get("cash_usd") or 0.0),
                  "positions": {p["symbol"]: float(p["quantity"]) for p in a["positions"]}}
        for a in snapshot["accounts"]
    }


def asset_classes(snapshot: dict[str, Any]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for a in snapshot["accounts"]:
        for p in a["positions"]:
            out.setdefault(p["symbol"], p.get("asset_class"))
    return out


def _f(x: float | None, nd: int = 4) -> float | None:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return None
    return round(float(x), nd)


def value_snapshot(snapshot: dict[str, Any], prices: dict[str, float]) -> dict[str, Any]:
    """Attach USD values and weights to every account and position."""
    accounts_out, positions_out = [], []
    total = 0.0
    for acct in snapshot["accounts"]:
        acct_value = float(acct.get("cash_usd") or 0.0)
        rows = []
        for pos in acct.get("positions", []):
            sym, qty = pos["symbol"], float(pos["quantity"])
            ac = pos.get("asset_class")
            if is_cash_like(sym, ac):
                price, priced = 1.0, True
            else:
                price = prices.get(sym)
                priced = price is not None
            value = qty * price if priced else None
            row = {
                "account_id": acct["id"], "account_type": acct.get("type", "taxable"),
                "symbol": sym, "asset_class": ac or infer_asset_class(sym), "quantity": qty,
                "price": _f(price, 4), "value_usd": _f(value, 2), "priced": priced,
                "cost_basis_usd": pos.get("cost_basis_usd"),
                "unrealized_pnl_usd": _f(value - float(pos["cost_basis_usd"]), 2)
                if priced and pos.get("cost_basis_usd") is not None else None,
            }
            rows.append(row)
            if priced:
                acct_value += value
        accounts_out.append({
            "id": acct["id"], "name": acct["name"], "type": acct.get("type", "taxable"),
            "cash_usd": float(acct.get("cash_usd") or 0.0), "value_usd": _f(acct_value, 2),
        })
        positions_out.extend(rows)
        total += acct_value

    for row in positions_out:
        row["weight"] = _f(row["value_usd"] / total, 4) if row["priced"] and total > 0 else None
    for a in accounts_out:
        a["weight"] = _f(a["value_usd"] / total, 4) if total > 0 else None
    return {"total_value_usd": _f(total, 2), "accounts": accounts_out, "positions": positions_out}


def combined_holdings(valued: dict[str, Any]) -> list[dict[str, Any]]:
    """Collapse positions across accounts into one row per symbol."""
    by_sym: dict[str, dict[str, Any]] = {}
    for p in valued["positions"]:
        row = by_sym.setdefault(p["symbol"], {
            "symbol": p["symbol"], "asset_class": p["asset_class"], "quantity": 0.0,
            "value_usd": 0.0, "weight": 0.0, "priced": p["priced"], "accounts": [],
        })
        row["quantity"] += p["quantity"]
        row["accounts"].append(p["account_id"])
        if p["priced"]:
            row["value_usd"] += p["value_usd"] or 0.0
            row["weight"] += p["weight"] or 0.0
        else:
            row["priced"] = False
    rows = sorted(by_sym.values(), key=lambda r: -(r["value_usd"] or 0))
    for r in rows:
        r["value_usd"], r["weight"] = _f(r["value_usd"], 2), _f(r["weight"], 4)
    return rows


def allocation(valued: dict[str, Any]) -> dict[str, Any]:
    total = valued["total_value_usd"] or 0.0
    by_class: dict[str, float] = {}
    by_account_type: dict[str, float] = {}
    cash = sum(a["cash_usd"] for a in valued["accounts"])
    for p in valued["positions"]:
        if p["priced"]:
            cls = "cash" if is_cash_like(p["symbol"], p["asset_class"]) else p["asset_class"]
            by_class[cls] = by_class.get(cls, 0.0) + p["value_usd"]
    by_class["cash"] = by_class.get("cash", 0.0) + cash
    for a in valued["accounts"]:
        by_account_type[a["type"]] = by_account_type.get(a["type"], 0.0) + (a["value_usd"] or 0.0)
    stock_sleeve = by_class.get("stock", 0.0)
    return {
        "by_asset_class": {k: {"value_usd": _f(v, 2), "weight": _f(v / total, 4) if total else None}
                           for k, v in sorted(by_class.items(), key=lambda kv: -kv[1])},
        "by_account_type": {k: {"value_usd": _f(v, 2), "weight": _f(v / total, 4) if total else None}
                            for k, v in by_account_type.items()},
        "single_stock_sleeve_weight": _f(stock_sleeve / total, 4) if total else None,
        "cash_weight": _f(by_class["cash"] / total, 4) if total else None,
    }


def position_stats(closes: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Trailing-window return, volatility and drawdown per symbol from closes."""
    out: dict[str, dict[str, Any]] = {}
    for sym in closes.columns:
        s = closes[sym].dropna()
        if len(s) < 5:
            continue
        rets = s.pct_change().dropna()
        peak = s.cummax()
        dd = (s / peak - 1.0).min()
        out[sym] = {
            "first_date": s.index[0].date().isoformat(), "last_date": s.index[-1].date().isoformat(),
            "sessions": int(len(s)), "period_return": _f(s.iloc[-1] / s.iloc[0] - 1.0),
            "annualized_vol": _f(rets.std() * math.sqrt(252)), "max_drawdown": _f(dd),
            "distance_from_high": _f(s.iloc[-1] / peak.iloc[-1] - 1.0),
        }
    return out


def risk_xray(closes: pd.DataFrame, weights: dict[str, float]) -> dict[str, Any]:
    from backtest.risk_xray import compute_risk_xray

    usable = {s: w for s, w in weights.items() if s in closes.columns and w > 0}
    if len(usable) < 2 or closes.empty:
        return {"warnings": ["fewer than two priced, invested positions with history; risk x-ray skipped"]}
    total = sum(usable.values())
    norm = {s: w / total for s, w in usable.items()}
    try:
        report = compute_risk_xray(closes[list(norm)], norm)
    except Exception as exc:  # noqa: BLE001 - report the gap, never fail the review
        return {"warnings": [f"risk x-ray failed: {exc}"]}
    keep = ("concentration", "volatility", "drawdown", "tail_risk", "diversification", "correlation", "warnings", "skipped")
    return {k: report.get(k) for k in keep if k in report}


def build_evidence(
    snapshot: dict[str, Any],
    closes: pd.DataFrame,
    benchmark_closes: pd.Series | None,
    unresolved: list[str],
    as_of: date,
) -> dict[str, Any]:
    prices = latest_closes(closes)
    valued = value_snapshot(snapshot, prices)
    holdings = combined_holdings(valued)
    weights = {h["symbol"]: h["weight"] for h in holdings
               if h["priced"] and h["weight"] and not is_cash_like(h["symbol"], h["asset_class"])}
    bench = None
    if benchmark_closes is not None and len(benchmark_closes.dropna()) >= 5:
        b = benchmark_closes.dropna()
        bench = {"symbol": str(b.name or "SPY"), "period_return": _f(b.iloc[-1] / b.iloc[0] - 1.0),
                 "first_date": b.index[0].date().isoformat(), "last_date": b.index[-1].date().isoformat()}
    gaps = [f"{s}: no price history retrieved; excluded from weights and risk" for s in unresolved]
    return {
        "as_of": as_of.isoformat(),
        "prices_as_of": closes.index[-1].date().isoformat() if not closes.empty else None,
        "total_value_usd": valued["total_value_usd"],
        "accounts": valued["accounts"],
        "positions": valued["positions"],
        "holdings": holdings,
        "allocation": allocation(valued),
        "position_stats": position_stats(closes),
        "risk": risk_xray(closes, weights),
        "benchmark": bench,
        "data_gaps": gaps,
    }
