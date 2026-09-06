"""Advisor service: push holdings, run a review, record decisions."""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Callable

import pandas as pd

from src.advisor import evidence as ev
from src.advisor.models import (
    DecisionIn, HoldingsIn, Objectives, ReviewOut, ReviewRequest, new_id,
)
from src.advisor.pricing import PriceFetcher, fetch_close_panel, is_cash_like, latest_closes, lookback_start
from src.advisor.prompt import build_messages, parse_review
from src.advisor.store import AdvisorStore

logger = logging.getLogger(__name__)

LLMFactory = Callable[[], Any]
_LLM_TIMEOUT_S = 180


class AdvisorError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _default_llm() -> Any:
    from src.providers.chat import ChatLLM

    return ChatLLM()


class AdvisorService:
    def __init__(
        self,
        store: AdvisorStore | None = None,
        *,
        price_fetcher: PriceFetcher | None = None,
        llm_factory: LLMFactory | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.store = store or AdvisorStore()
        self._fetch = price_fetcher
        self._llm_factory = llm_factory or _default_llm
        self._now = now or (lambda: datetime.now(timezone.utc))

    def now_iso(self) -> str:
        return self._now().replace(microsecond=0).isoformat()

    def today(self) -> date:
        return self._now().date()

    # ── holdings ──────────────────────────────────────────────────────────
    def push_holdings(self, holdings: HoldingsIn) -> dict[str, Any]:
        snapshot = {
            "id": new_id("snap"), "created_at": self.now_iso(), "source": holdings.source,
            "as_of": holdings.as_of, "accounts": [a.model_dump() for a in holdings.accounts],
        }
        self.store.save_snapshot(snapshot)
        closes, unresolved = self._panel(snapshot, days=10)
        valued = ev.value_snapshot(snapshot, latest_closes(closes))
        return {
            "snapshot_id": snapshot["id"], "created_at": snapshot["created_at"],
            "prices_as_of": closes.index[-1].date().isoformat() if not closes.empty else None,
            "total_value_usd": valued["total_value_usd"], "accounts": valued["accounts"],
            "holdings": ev.combined_holdings(valued), "allocation": ev.allocation(valued),
            "data_gaps": [f"{s}: no price retrieved" for s in unresolved],
        }

    def latest_holdings(self) -> dict[str, Any]:
        snap = self.store.latest_snapshot()
        if not snap:
            raise AdvisorError("no holdings pushed yet", 404)
        return snap

    # ── review ────────────────────────────────────────────────────────────
    def review(self, req: ReviewRequest) -> dict[str, Any]:
        snapshot = self.store.get_snapshot(req.snapshot_id) if req.snapshot_id else self.store.latest_snapshot()
        if not snapshot:
            raise AdvisorError("no holdings snapshot to review; push holdings first", 404)
        today = self.today()
        objectives = req.objectives
        closes, unresolved = self._panel(snapshot, days=ev.LOOKBACK_DAYS, extra={objectives.benchmark: "etf"})
        bench = closes.pop(objectives.benchmark) if objectives.benchmark in closes.columns else None
        unresolved = [s for s in unresolved if s != objectives.benchmark]
        evidence = ev.build_evidence(snapshot, closes, bench, unresolved, today)
        if bench is None:
            evidence["data_gaps"].append(f"{objectives.benchmark}: benchmark history not retrieved")

        review_out, model = self._ask(objectives, evidence)
        prices = latest_closes(closes)
        recs = self._price_recommendations(review_out, snapshot, prices, today)
        book = apply_recommendations(snapshot, prices, recs)

        review = {
            "id": new_id("rev"), "created_at": self.now_iso(), "snapshot_id": snapshot["id"],
            "objectives": objectives.model_dump(), "model": model,
            "prices_as_of": evidence["prices_as_of"], "total_value_usd": evidence["total_value_usd"],
            "summary": review_out.summary,
            "allocation_findings": review_out.allocation_findings,
            "risk_findings": review_out.risk_findings,
            "tax_findings": review_out.tax_findings,
            "watchlist": review_out.watchlist,
            "data_gaps": evidence["data_gaps"] + review_out.data_gaps,
            "allocation": evidence["allocation"], "risk": evidence["risk"], "benchmark": evidence["benchmark"],
            "hypothetical_book": book,
            "recommendation_ids": [r["id"] for r in recs],
        }
        self.store.save_review(review, recs)
        return {**review, "recommendations": recs}

    def _ask(self, objectives: Objectives, evidence: dict[str, Any]) -> tuple[ReviewOut, str | None]:
        messages = build_messages(objectives, evidence)
        llm = self._llm_factory()
        try:
            model = getattr(llm, "model_name", None)
            last_error: str | None = None
            for attempt in range(2):
                msgs = messages if attempt == 0 else messages + [
                    {"role": "user", "content": f"Your previous reply was rejected: {last_error}. "
                                                "Return only the corrected JSON object."}]
                resp = llm.chat(msgs, tools=None, timeout=_LLM_TIMEOUT_S)
                try:
                    return parse_review(resp.content or ""), model
                except ValueError as exc:
                    last_error = str(exc)
                    logger.warning("advisor reply rejected (attempt %d): %s", attempt + 1, exc)
            raise AdvisorError(f"model did not return a valid review: {last_error}", 502)
        finally:
            close = getattr(llm, "close", None)
            if callable(close):
                close()

    def _price_recommendations(self, out: ReviewOut, snapshot: dict[str, Any], prices: dict[str, float],
                               today: date) -> list[dict[str, Any]]:
        held = {p["symbol"]: p.get("asset_class") for a in snapshot["accounts"] for p in a["positions"]}
        missing = {r.symbol: None for r in out.recommendations if r.symbol not in prices and not is_cash_like(r.symbol, held.get(r.symbol))}
        if missing:
            extra, _ = fetch_close_panel(missing, lookback_start(today, 10), today, self._fetch)
            prices = {**prices, **latest_closes(extra)}
        recs: list[dict[str, Any]] = []
        created = self.now_iso()
        for r in out.recommendations:
            if r.action != "buy" and r.symbol not in held:
                logger.warning("dropping %s recommendation for %s: not in holdings", r.action, r.symbol)
                continue
            price = prices.get(r.symbol)
            recs.append({
                "id": new_id("rec"), "created_at": created, "status": "open",
                **r.model_dump(),
                "is_new_position": r.symbol not in held,
                "price_at_rec": round(price, 4) if price is not None else None,
                "priced": price is not None,
                "quantity": None, "resolved_account_id": r.account_id,
            })
        return recs

    # ── decisions ─────────────────────────────────────────────────────────
    def decide(self, rec_id: str, decision: DecisionIn) -> dict[str, Any]:
        rec = self.store.decide(rec_id, decision.status, decision.note, self.now_iso())
        if not rec:
            raise AdvisorError("recommendation not found", 404)
        return rec

    # ── helpers ───────────────────────────────────────────────────────────
    def _panel(self, snapshot: dict[str, Any], *, days: int, extra: dict[str, str | None] | None = None
               ) -> tuple[pd.DataFrame, list[str]]:
        symbols: dict[str, str | None] = {}
        for acct in snapshot["accounts"]:
            for p in acct["positions"]:
                symbols.setdefault(p["symbol"], p.get("asset_class"))
        symbols.update(extra or {})
        today = self.today()
        return fetch_close_panel(symbols, lookback_start(today, days), today, self._fetch)


def apply_recommendations(snapshot: dict[str, Any], prices: dict[str, float],
                          recs: list[dict[str, Any]]) -> dict[str, Any]:
    """Turn recommendations into a hypothetical book and fill in each rec's
    resolved account and quantity in place.

    The hypothetical book starts identical in value to the actual book and
    differs only by the recommended trades, so later divergence is purely the
    result of the advice.
    """
    book: dict[str, dict[str, Any]] = {
        a["id"]: {"type": a.get("type", "taxable"), "cash_usd": float(a.get("cash_usd") or 0.0),
                  "positions": {p["symbol"]: float(p["quantity"]) for p in a["positions"]},
                  "asset_class": {p["symbol"]: p.get("asset_class") for p in a["positions"]}}
        for a in snapshot["accounts"]
    }
    total = sum(acct["cash_usd"] + sum(q * prices.get(s, 1.0 if is_cash_like(s, acct["asset_class"].get(s)) else 0.0)
                                        for s, q in acct["positions"].items()) for acct in book.values())

    def symbol_value(sym: str) -> float:
        return sum(a["positions"].get(sym, 0.0) for a in book.values()) * prices.get(sym, 0.0)

    for rec in recs:
        price = rec.get("price_at_rec")
        if rec["action"] == "hold" or not price:
            continue
        sym = rec["symbol"]
        acct_id = rec.get("account_id") if rec.get("account_id") in book else None
        if rec["action"] == "buy":
            acct_id = acct_id or max(book, key=lambda k: book[k]["cash_usd"])
            amount = rec.get("amount_usd")
            if amount is None and rec.get("target_weight") is not None:
                amount = rec["target_weight"] * total - symbol_value(sym)
            if not amount or amount <= 0:
                continue
            qty = amount / price
            book[acct_id]["cash_usd"] -= amount
            book[acct_id]["positions"][sym] = book[acct_id]["positions"].get(sym, 0.0) + qty
        else:  # sell / trim
            holders = [k for k, a in book.items() if a["positions"].get(sym, 0.0) > 0]
            if not holders:
                continue
            acct_id = acct_id if acct_id in holders else max(holders, key=lambda k: book[k]["positions"][sym])
            held = book[acct_id]["positions"][sym]
            if rec["action"] == "sell":
                qty = held
            else:
                amount = rec.get("amount_usd")
                if amount is None and rec.get("target_weight") is not None:
                    amount = symbol_value(sym) - rec["target_weight"] * total
                if not amount or amount <= 0:
                    continue
                qty = min(held, amount / price)
            book[acct_id]["cash_usd"] += qty * price
            remaining = held - qty
            if remaining <= 1e-9:
                book[acct_id]["positions"].pop(sym, None)
            else:
                book[acct_id]["positions"][sym] = remaining
            amount = qty * price
        rec["resolved_account_id"] = acct_id
        rec["quantity"] = round(qty, 6)
        rec["amount_usd"] = round(amount, 2)

    return {k: {"type": a["type"], "cash_usd": round(a["cash_usd"], 2),
                "positions": {s: round(q, 6) for s, q in a["positions"].items()}}
            for k, a in book.items()}
