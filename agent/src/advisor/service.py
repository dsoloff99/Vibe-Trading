"""Advisor service: push holdings, run a review, record decisions, track results."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

import pandas as pd

from src.advisor import evidence as ev
from src.advisor.evidence import asset_classes, book_from_snapshot
from src.advisor.models import DecisionIn, HoldingsIn, Objectives, ReviewOut, ReviewRequest, new_id
from src.advisor.pricing import PriceFetcher, fetch_close_panel, is_cash_like, latest_closes
from src.advisor.prompt import build_messages, parse_review
from src.advisor.store import AdvisorStore
from src.advisor.tracker import review_performance, scorecard

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
        closes, unresolved = self._panel(asset_classes(snapshot), days=10)
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
        objectives = req.objectives
        held = asset_classes(snapshot)
        benchmark = objectives.benchmark
        closes, unresolved = self._panel({**held, benchmark: held.get(benchmark, "etf")}, days=ev.LOOKBACK_DAYS)
        bench = closes[benchmark] if benchmark in closes.columns else None
        # The benchmark stays in the panel when it is also a holding; otherwise
        # it is evidence only and must not appear as a position.
        panel = closes if benchmark in held else closes.drop(columns=[benchmark], errors="ignore")
        gaps = [s for s in unresolved if s in held]
        evidence = ev.build_evidence(snapshot, panel, bench, gaps, self.today())
        if bench is None:
            evidence["data_gaps"].append(f"{benchmark}: benchmark history not retrieved")

        review_out, model = self._ask(objectives, evidence)
        prices = latest_closes(panel)
        recs = self._price_recommendations(review_out, snapshot, held, prices)
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
        }
        self.store.save_review(review, recs)
        return {**review, "recommendations": recs}

    def _ask(self, objectives: Objectives, evidence: dict[str, Any]) -> tuple[ReviewOut, str | None]:
        messages = build_messages(objectives, evidence)
        llm = self._llm_factory()
        try:
            model = getattr(llm, "model_name", None)
            last_error = ""
            for attempt in range(2):
                resp = llm.chat(messages, tools=None, timeout=_LLM_TIMEOUT_S)
                content = resp.content or ""
                try:
                    return parse_review(content), model
                except ValueError as exc:
                    last_error = str(exc)
                    logger.warning("advisor reply rejected (attempt %d): %s", attempt + 1, exc)
                    messages = messages + [
                        {"role": "assistant", "content": content},
                        {"role": "user", "content": f"That reply was rejected: {last_error}. "
                                                    "Return only the corrected JSON object."},
                    ]
            raise AdvisorError(f"model did not return a valid review: {last_error}", 502)
        finally:
            close = getattr(llm, "close", None)
            if callable(close):
                close()

    def _price_recommendations(self, out: ReviewOut, snapshot: dict[str, Any], held: dict[str, str | None],
                               prices: dict[str, float]) -> list[dict[str, Any]]:
        """Attach our own price to each recommendation and drop the invalid ones."""
        missing = {r.symbol: None for r in out.recommendations
                   if r.symbol not in prices and not is_cash_like(r.symbol, held.get(r.symbol))}
        if missing:
            extra, _ = self._panel(missing, days=10)
            prices = {**prices, **latest_closes(extra)}
        account_ids = {a["id"] for a in snapshot["accounts"]}
        recs: list[dict[str, Any]] = []
        created = self.now_iso()
        for r in out.recommendations:
            if r.action != "buy" and r.symbol not in held:
                logger.warning("dropping %s recommendation for %s: not in holdings", r.action, r.symbol)
                continue
            price = 1.0 if is_cash_like(r.symbol, held.get(r.symbol)) else prices.get(r.symbol)
            recs.append({
                "id": new_id("rec"), "created_at": created, "status": "open",
                **r.model_dump(),
                "is_new_position": r.symbol not in held,
                "price_at_rec": round(price, 4) if price is not None else None,
                "priced": price is not None,
                "quantity": None,
                "resolved_account_id": r.account_id if r.account_id in account_ids else None,
            })
        return recs

    # ── decisions ─────────────────────────────────────────────────────────
    def decide(self, rec_id: str, decision: DecisionIn) -> dict[str, Any]:
        rec = self.store.decide(rec_id, decision.status, decision.note, self.now_iso())
        if not rec:
            raise AdvisorError("recommendation not found", 404)
        return rec

    # ── tracking ──────────────────────────────────────────────────────────
    def performance(self, review_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        """One price fetch for every review's symbols since the earliest review,
        sliced per review, so the finance app can poll this cheaply."""
        reviews = [self.store.get_review(review_id)] if review_id else self.store.list_reviews(limit)
        if review_id and not reviews[0]:
            raise AdvisorError("review not found", 404)
        if not reviews:
            return {"scorecard": scorecard([]), "reviews": []}
        items = []
        symbols: dict[str, str | None] = {}
        for review in reviews:
            snapshot = self.store.get_snapshot(review["snapshot_id"]) or {"accounts": []}
            recs = self.store.list_recommendations(review_id=review["id"])
            classes = asset_classes(snapshot)
            for sym in [*classes, *(s for a in review["hypothetical_book"].values() for s in a["positions"]),
                        *(r["symbol"] for r in recs)]:
                symbols.setdefault(sym, classes.get(sym))
            symbols.setdefault(review["objectives"].get("benchmark", "SPY"), "etf")
            items.append((review, snapshot, recs))
        earliest = min(date.fromisoformat(r["created_at"][:10]) for r, _, _ in items)
        closes, unresolved = fetch_close_panel(symbols, earliest, self.today(), self._fetch)
        per_review = [review_performance(review, snapshot, recs, closes, unresolved) for review, snapshot, recs in items]
        return {"scorecard": scorecard(per_review), "reviews": per_review}

    # ── helpers ───────────────────────────────────────────────────────────
    def _panel(self, symbols: dict[str, str | None], *, days: int) -> tuple[pd.DataFrame, list[str]]:
        today = self.today()
        return fetch_close_panel(symbols, today - timedelta(days=days), today, self._fetch)


def apply_recommendations(snapshot: dict[str, Any], prices: dict[str, float],
                          recs: list[dict[str, Any]]) -> dict[str, Any]:
    """Turn recommendations into the advised book and fill in each rec's
    resolved account, quantity and dollar amount in place.

    The advised book starts identical in value to the actual book and differs
    only by the recommended trades, so later divergence is purely the result
    of the advice. Sells and trims drain holdings largest-account-first when
    the symbol sits in several accounts.
    """
    book = book_from_snapshot(snapshot)
    classes = asset_classes(snapshot)

    def price_of(sym: str) -> float:
        return 1.0 if is_cash_like(sym, classes.get(sym)) else prices.get(sym, 0.0)

    def symbol_value(sym: str) -> float:
        return sum(a["positions"].get(sym, 0.0) for a in book.values()) * price_of(sym)

    total = sum(a["cash_usd"] + sum(q * price_of(s) for s, q in a["positions"].items()) for a in book.values())

    for rec in recs:
        price = rec.get("price_at_rec")
        sym, action = rec["symbol"], rec["action"]
        holders = sorted((k for k, a in book.items() if a["positions"].get(sym, 0.0) > 0),
                         key=lambda k: -book[k]["positions"][sym])
        preferred = rec.get("resolved_account_id")
        if action == "hold" or not price:
            rec["resolved_account_id"] = preferred if preferred in holders else (holders[0] if holders else preferred)
            continue
        if action == "buy":
            acct_id = preferred if preferred in book else max(book, key=lambda k: book[k]["cash_usd"])
            amount = rec.get("amount_usd")
            if amount is None and rec.get("target_weight") is not None:
                amount = rec["target_weight"] * total - symbol_value(sym)
            if not amount or amount <= 0:
                rec["resolved_account_id"] = acct_id
                continue
            qty = amount / price
            book[acct_id]["cash_usd"] -= amount
            book[acct_id]["positions"][sym] = book[acct_id]["positions"].get(sym, 0.0) + qty
            rec.update(resolved_account_id=acct_id, quantity=round(qty, 6), amount_usd=round(amount, 2))
            continue
        # sell / trim: an explicit amount or target weight is a partial sale; a bare sell is the whole position.
        if not holders:
            continue
        amount = rec.get("amount_usd")
        if amount is None and rec.get("target_weight") is not None:
            amount = symbol_value(sym) - rec["target_weight"] * total
        if amount is None and action == "sell":
            amount = symbol_value(sym)
        if not amount or amount <= 0:
            rec["resolved_account_id"] = preferred if preferred in holders else holders[0]
            continue
        order = [preferred] + [h for h in holders if h != preferred] if preferred in holders else holders
        remaining_qty, sold_qty, touched = amount / price, 0.0, []
        for acct_id in order:
            held = book[acct_id]["positions"][sym]
            qty = min(held, remaining_qty)
            if qty <= 0:
                continue
            book[acct_id]["cash_usd"] += qty * price
            if held - qty <= 1e-9:
                book[acct_id]["positions"].pop(sym, None)
            else:
                book[acct_id]["positions"][sym] = held - qty
            sold_qty += qty
            remaining_qty -= qty
            touched.append(acct_id)
            if remaining_qty <= 1e-9:
                break
        rec.update(resolved_account_id=touched[0], quantity=round(sold_qty, 6), amount_usd=round(sold_qty * price, 2))

    return {k: {"type": a["type"], "cash_usd": round(a["cash_usd"], 2),
                "positions": {s: round(q, 6) for s, q in a["positions"].items()}}
            for k, a in book.items()}
