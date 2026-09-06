"""Advisor: holdings push, wealth-manager review, recommendation tracking.

Runs fully offline: prices come from a deterministic synthetic fetcher and the
LLM is a stub returning a fixed JSON review.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.advisor import prompt as prompt_mod
from src.advisor.models import DecisionIn, HoldingsIn, ReviewRequest
from src.advisor.pricing import fetch_close_panel, loader_symbol
from src.advisor.service import AdvisorService, apply_recommendations
from src.advisor.store import AdvisorStore
from src.advisor.tracker import score_recommendation, scorecard
from src.api import advisor_routes

TODAY = date(2026, 9, 4)
NOW = datetime(2026, 9, 4, 21, 0, tzinfo=timezone.utc)

# Deterministic daily-drift prices per loader symbol: (start price, daily drift).
_PRICES = {
    "AAPL.US": (200.0, 0.001), "NVDA.US": (150.0, 0.003), "VTI.US": (300.0, 0.0005),
    "BND.US": (72.0, 0.0), "SPY.US": (600.0, 0.0008), "BTC-USDT": (60000.0, 0.002),
    "COST.US": (900.0, 0.001),
}


def fake_fetch(codes, start, end):
    """Synthetic close records for every known code in [start, end]."""
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    out = {}
    for code in codes:
        if code not in _PRICES:
            continue
        p0, drift = _PRICES[code]
        rows = []
        d = s
        while d <= e:
            if d.weekday() < 5:
                days = (d - date(2025, 1, 1)).days
                rows.append({"date": d.isoformat(), "close": p0 * (1 + drift) ** days})
            d += timedelta(days=1)
        out[code] = rows
    return out


def price_on(code: str, day: date) -> float:
    p0, drift = _PRICES[code]
    return p0 * (1 + drift) ** ((day - date(2025, 1, 1)).days)


HOLDINGS = {
    "accounts": [
        {"id": "schwab-taxable", "name": "Schwab Individual", "type": "taxable", "cash_usd": 5000,
         "positions": [{"symbol": "AAPL", "quantity": 50, "cost_basis_usd": 6000},
                       {"symbol": "NVDA", "quantity": 100, "cost_basis_usd": 4000},
                       {"symbol": "VTI", "quantity": 40, "asset_class": "etf"}]},
        {"id": "schwab-roth", "name": "Schwab Roth IRA", "type": "roth_ira", "cash_usd": 1000,
         "positions": [{"symbol": "VTI", "quantity": 30, "asset_class": "etf"},
                       {"symbol": "BND", "quantity": 100, "asset_class": "etf"}]},
        {"id": "robinhood", "name": "Robinhood", "type": "crypto", "cash_usd": 0,
         "positions": [{"symbol": "BTC", "quantity": 0.1, "asset_class": "crypto"},
                       {"symbol": "ZZZZ", "quantity": 10}]},
    ],
    "source": "test",
}

REVIEW_JSON = {
    "summary": "The stock sleeve is above the 40% cap because NVDA has run; trim it and add to the core.",
    "allocation_findings": ["Individual stocks exceed the 40% cap."],
    "risk_findings": ["NVDA drives most of the volatility."],
    "tax_findings": ["NVDA lots in taxable are long-term; trimming realizes long-term gains."],
    "recommendations": [
        {"action": "trim", "symbol": "NVDA", "amount_usd": 5000, "rationale": "Reduce single-name concentration below the position cap.", "confidence": 0.7, "tax_note": "Long-term gain."},
        {"action": "buy", "symbol": "VTI", "account_id": "schwab-roth", "amount_usd": 3000, "rationale": "Redeploy into the tax-sheltered core index position.", "confidence": 0.8},
        {"action": "buy", "symbol": "COST", "amount_usd": 2000, "rationale": "Quality compounder for the stock sleeve at a reasonable multiple.", "confidence": 0.55, "is_new_position": True},
        {"action": "hold", "symbol": "AAPL", "rationale": "Thesis intact; position within limits.", "confidence": 0.6},
        {"action": "sell", "symbol": "TSLA", "rationale": "Not held, should be dropped by the validator.", "confidence": 0.9},
    ],
    "watchlist": ["MSFT"],
    "data_gaps": [],
}


class FakeLLM:
    model_name = "fake-model"

    def __init__(self, replies):
        self._replies = list(replies)
        self.seen: list[list[dict]] = []

    def chat(self, messages, tools=None, timeout=None):
        self.seen.append(list(messages))
        return SimpleNamespace(content=self._replies.pop(0))

    def close(self):
        pass


@pytest.fixture
def service(tmp_path):
    return AdvisorService(
        AdvisorStore(tmp_path / "advisor.sqlite3"), price_fetcher=fake_fetch,
        llm_factory=lambda: FakeLLM([json.dumps(REVIEW_JSON)]), now=lambda: NOW,
    )


# ── pricing ───────────────────────────────────────────────────────────────────

def test_loader_symbol_mapping():
    assert loader_symbol("AAPL") == "AAPL.US"
    assert loader_symbol("BTC") == "BTC-USDT"
    assert loader_symbol("BTC", "crypto") == "BTC-USDT"
    assert loader_symbol("AAPL.US") == "AAPL.US"
    assert loader_symbol("^SPX") == "^SPX"


def test_fetch_close_panel_keys_by_app_symbol_and_reports_gaps():
    closes, unresolved = fetch_close_panel({"AAPL": None, "BTC": "crypto", "ZZZZ": None, "USDC": None},
                                           TODAY - timedelta(days=10), TODAY, fake_fetch)
    assert set(closes.columns) == {"AAPL", "BTC"}
    assert unresolved == ["ZZZZ"]
    assert closes["AAPL"].iloc[-1] == pytest.approx(price_on("AAPL.US", TODAY))


# ── holdings push ─────────────────────────────────────────────────────────────

def test_push_holdings_values_accounts_and_flags_gaps(service):
    out = service.push_holdings(HoldingsIn(**HOLDINGS))
    assert out["snapshot_id"].startswith("snap_")
    assert out["prices_as_of"] == TODAY.isoformat()
    aapl = price_on("AAPL.US", TODAY)
    expected_total = (5000 + 50 * aapl + 100 * price_on("NVDA.US", TODAY) + 70 * price_on("VTI.US", TODAY)
                      + 1000 + 100 * price_on("BND.US", TODAY) + 0.1 * price_on("BTC-USDT", TODAY))
    assert out["total_value_usd"] == pytest.approx(expected_total, rel=1e-6)
    assert out["data_gaps"] == ["ZZZZ: no price retrieved"]
    vti = next(h for h in out["holdings"] if h["symbol"] == "VTI")
    assert vti["quantity"] == 70 and set(vti["accounts"]) == {"schwab-taxable", "schwab-roth"}
    assert out["allocation"]["by_account_type"]["roth_ira"]["weight"] > 0
    assert service.store.latest_snapshot()["id"] == out["snapshot_id"]


# ── review ────────────────────────────────────────────────────────────────────

def test_review_prices_recommendations_and_builds_hypothetical_book(service):
    service.push_holdings(HoldingsIn(**HOLDINGS))
    review = service.review(ReviewRequest())
    assert review["model"] == "fake-model"
    assert review["summary"].startswith("The stock sleeve")
    assert "ZZZZ: no price history retrieved; excluded from weights and risk" in review["data_gaps"]
    assert review["benchmark"]["symbol"] == "SPY"
    assert review["risk"]["concentration"]["hhi"] > 0

    recs = {r["symbol"]: r for r in review["recommendations"]}
    assert "TSLA" not in recs, "sell of an unheld symbol must be dropped"
    assert set(recs) == {"NVDA", "VTI", "COST", "AAPL"}

    nvda = recs["NVDA"]
    assert nvda["price_at_rec"] == pytest.approx(price_on("NVDA.US", TODAY), rel=1e-4)
    assert nvda["resolved_account_id"] == "schwab-taxable"
    assert nvda["quantity"] == pytest.approx(5000 / nvda["price_at_rec"], rel=1e-4)

    cost = recs["COST"]
    assert cost["is_new_position"] is True and cost["priced"] is True
    assert cost["resolved_account_id"] == "schwab-taxable"  # most cash
    assert recs["AAPL"]["quantity"] is None and recs["AAPL"]["resolved_account_id"] == "schwab-taxable"  # hold is a no-op

    book = review["hypothetical_book"]
    assert book["schwab-roth"]["positions"]["VTI"] == pytest.approx(30 + 3000 / price_on("VTI.US", TODAY), rel=1e-4)
    assert book["schwab-roth"]["cash_usd"] == pytest.approx(1000 - 3000)
    assert book["schwab-taxable"]["positions"]["COST"] > 0
    assert book["schwab-taxable"]["positions"]["NVDA"] == pytest.approx(100 - nvda["quantity"], rel=1e-4)
    assert book["schwab-taxable"]["cash_usd"] == pytest.approx(5000 + 5000 - 2000)

    stored = service.store.list_recommendations(review_id=review["id"])
    assert len(stored) == 4 and all(r["status"] == "open" for r in stored)


def test_review_retries_once_on_bad_json(tmp_path):
    llm = FakeLLM(["not json at all", "Sure, here it is:\n```json\n" + json.dumps(REVIEW_JSON) + "\n```\nLet me know."])
    svc = AdvisorService(AdvisorStore(tmp_path / "a.sqlite3"), price_fetcher=fake_fetch, now=lambda: NOW, llm_factory=lambda: llm)
    svc.push_holdings(HoldingsIn(**HOLDINGS))
    review = svc.review(ReviewRequest())
    assert len(review["recommendations"]) == 4
    retry = llm.seen[1]
    assert retry[-2] == {"role": "assistant", "content": "not json at all"} and "rejected" in retry[-1]["content"]


def test_review_keeps_a_held_benchmark_priced(tmp_path):
    holdings = {"accounts": [{"id": "a", "name": "A", "type": "taxable", "cash_usd": 0,
                              "positions": [{"symbol": "SPY", "quantity": 10, "asset_class": "etf"},
                                            {"symbol": "AAPL", "quantity": 10}]}]}
    out = {**REVIEW_JSON, "recommendations": []}
    svc = AdvisorService(AdvisorStore(tmp_path / "a.sqlite3"), price_fetcher=fake_fetch, now=lambda: NOW,
                         llm_factory=lambda: FakeLLM([json.dumps(out)]))
    svc.push_holdings(HoldingsIn(**holdings))
    review = svc.review(ReviewRequest())
    assert review["total_value_usd"] == pytest.approx(10 * price_on("SPY.US", TODAY) + 10 * price_on("AAPL.US", TODAY), rel=1e-6)
    assert review["benchmark"]["symbol"] == "SPY" and not review["data_gaps"]


def test_cash_like_recommendation_is_priced_at_one(tmp_path):
    holdings = {"accounts": [{"id": "a", "name": "A", "type": "crypto", "cash_usd": 0,
                              "positions": [{"symbol": "USDC", "quantity": 500, "asset_class": "cash"},
                                            {"symbol": "BTC", "quantity": 0.1, "asset_class": "crypto"}]}]}
    out = {**REVIEW_JSON, "recommendations": [
        {"action": "sell", "symbol": "USDC", "amount_usd": 200, "rationale": "Move idle stablecoin into the core.", "confidence": 0.6}]}
    svc = AdvisorService(AdvisorStore(tmp_path / "a.sqlite3"), price_fetcher=fake_fetch, now=lambda: NOW,
                         llm_factory=lambda: FakeLLM([json.dumps(out)]))
    svc.push_holdings(HoldingsIn(**holdings))
    rec = svc.review(ReviewRequest())["recommendations"][0]
    assert rec["price_at_rec"] == 1.0 and rec["quantity"] == 200 and rec["resolved_account_id"] == "a"


def test_review_requires_holdings(service):
    from src.advisor.service import AdvisorError
    with pytest.raises(AdvisorError) as exc:
        service.review(ReviewRequest())
    assert exc.value.status_code == 404


def test_prompt_embeds_schema_mandate_and_evidence():
    msgs = prompt_mod.build_messages(ReviewRequest().objectives, {"total_value_usd": 123456.78})
    assert '"recommendations"' in msgs[0]["content"] and "single_stock_sleeve_cap" in msgs[1]["content"]
    assert "123456.78" in msgs[1]["content"]
    assert "Rebalancing" in msgs[0]["content"] and "Tax Impact" in msgs[0]["content"]


def test_parse_review_rejects_schema_violations():
    bad = {**REVIEW_JSON, "recommendations": [{"action": "short", "symbol": "X", "rationale": "long enough text here", "confidence": 0.5}]}
    with pytest.raises(ValueError):
        prompt_mod.parse_review(json.dumps(bad))


def test_apply_recommendations_target_weight_and_full_sell():
    snapshot = {"accounts": [{"id": "a", "type": "taxable", "cash_usd": 1000,
                              "positions": [{"symbol": "AAPL", "quantity": 10}, {"symbol": "VTI", "quantity": 10}]}]}
    prices = {"AAPL": 100.0, "VTI": 100.0}  # total 3000
    recs = [
        {"action": "trim", "symbol": "AAPL", "target_weight": 0.2, "price_at_rec": 100.0},   # 1000 -> 600: sell 4
        {"action": "sell", "symbol": "VTI", "price_at_rec": 100.0},
        {"action": "buy", "symbol": "MSFT", "target_weight": 0.1, "price_at_rec": 50.0},    # 300 -> 6 shares
        {"action": "buy", "symbol": "AAPL", "target_weight": 0.1, "price_at_rec": 100.0, "account_id": "zzz"},  # already above target: no-op
    ]
    book = apply_recommendations(snapshot, prices, recs)
    assert book["a"]["positions"] == {"AAPL": 6.0, "MSFT": 6.0}
    assert book["a"]["cash_usd"] == pytest.approx(1000 + 400 + 1000 - 300)
    assert recs[0]["quantity"] == 4 and recs[1]["quantity"] == 10 and recs[2]["amount_usd"] == 300
    assert recs[3].get("quantity") is None and recs[3]["resolved_account_id"] == "a"


def test_apply_recommendations_partial_sell_drains_accounts_largest_first():
    snapshot = {"accounts": [
        {"id": "a", "type": "taxable", "cash_usd": 0, "positions": [{"symbol": "VTI", "quantity": 40}]},
        {"id": "b", "type": "roth_ira", "cash_usd": 0, "positions": [{"symbol": "VTI", "quantity": 30}]},
    ]}
    recs = [{"action": "sell", "symbol": "VTI", "amount_usd": 5000, "price_at_rec": 100.0},   # 50 shares: 40 from a, 10 from b
            {"action": "sell", "symbol": "VTI", "price_at_rec": 100.0}]                        # the rest
    book = apply_recommendations(snapshot, {"VTI": 100.0}, recs)
    assert recs[0]["quantity"] == 50 and recs[0]["amount_usd"] == 5000 and recs[0]["resolved_account_id"] == "a"
    assert recs[1]["quantity"] == 20 and recs[1]["resolved_account_id"] == "b"
    assert book["a"] == {"type": "taxable", "cash_usd": 4000.0, "positions": {}}
    assert book["b"] == {"type": "roth_ira", "cash_usd": 3000.0, "positions": {}}


# ── decisions and tracking ────────────────────────────────────────────────────

def test_decide_updates_status(service):
    service.push_holdings(HoldingsIn(**HOLDINGS))
    rec = service.review(ReviewRequest())["recommendations"][0]
    out = service.decide(rec["id"], DecisionIn(status="accepted", note="done in Schwab"))
    assert out["status"] == "accepted" and out["note"] == "done in Schwab" and out["decided_at"]
    assert service.store.list_recommendations(status="accepted")[0]["id"] == rec["id"]


def test_score_recommendation_direction():
    assert score_recommendation({"action": "buy", "price_at_rec": 100}, 110, 0.05)["excess"] == pytest.approx(0.05)
    assert score_recommendation({"action": "trim", "price_at_rec": 100}, 110, 0.05)["excess"] == pytest.approx(-0.05)
    assert score_recommendation({"action": "sell", "price_at_rec": 100}, 90, 0.05)["hit"] is True
    assert score_recommendation({"action": "buy", "price_at_rec": None}, 90, 0.05)["hit"] is None


def test_review_performance_marks_both_books_against_spy(service):
    service.push_holdings(HoldingsIn(**HOLDINGS))
    service.review(ReviewRequest())
    service._now = lambda: NOW + timedelta(days=30)
    out = service.performance()
    perf = out["reviews"][0]
    assert perf["status"] == "ok" and perf["since"] == TODAY.isoformat()
    assert perf["curve"][0]["actual"] == pytest.approx(perf["curve"][0]["hypothetical"], rel=1e-6), \
        "both books start at the same value on the review date"
    assert perf["curve"][-1]["date"] == "2026-10-02"
    # NVDA drifts fastest, so trimming it costs value: the advice delta is negative here.
    assert perf["advice_delta_usd"] < 0
    nvda = next(r for r in perf["recommendations"] if r["symbol"] == "NVDA")
    assert nvda["hit"] is False and nvda["symbol_return"] > nvda["benchmark_return"]
    card = out["scorecard"]
    assert card["scored_recommendations"] == 3, "holds are reported but do not count toward the hit rate"
    assert 0 <= card["hit_rate"] <= 1 and "trim" in card["by_action"] and "hold" in card["by_action"]
    assert json.dumps(out, allow_nan=False)


def test_performance_stays_finite_when_a_symbol_starts_trading_after_the_review(service):
    """A recommended new position with no history on the review date must not
    poison the curves with NaN (the route would 500 on serialisation)."""
    service.push_holdings(HoldingsIn(**HOLDINGS))
    review = service.review(ReviewRequest())
    late_start = TODAY + timedelta(days=7)

    def gappy_fetch(codes, start, end):
        out = fake_fetch(codes, start, end)
        out["COST.US"] = [r for r in out.get("COST.US", []) if date.fromisoformat(r["date"]) >= late_start]
        return out

    service._fetch = gappy_fetch
    service._now = lambda: NOW + timedelta(days=30)
    out = service.performance(review["id"])
    perf = out["reviews"][0]
    assert perf["status"] == "ok"
    assert json.dumps(out, allow_nan=False)
    assert perf["curve"][0]["actual"] == pytest.approx(perf["curve"][0]["hypothetical"], rel=1e-6)


def test_performance_with_no_reviews_is_empty(service):
    assert service.performance() == {"scorecard": scorecard([]), "reviews": []}


# ── routes ────────────────────────────────────────────────────────────────────

@pytest.fixture
def client(tmp_path, monkeypatch):
    svc = AdvisorService(AdvisorStore(tmp_path / "advisor.sqlite3"), price_fetcher=fake_fetch,
                         llm_factory=lambda: FakeLLM([json.dumps(REVIEW_JSON)]), now=lambda: NOW)
    monkeypatch.setattr(advisor_routes, "_service", svc)
    app = FastAPI()
    advisor_routes.register_advisor_routes(app)
    return TestClient(app)


def test_routes_end_to_end(client):
    assert client.post("/advisor/review").status_code == 404
    r = client.post("/advisor/holdings", json=HOLDINGS)
    assert r.status_code == 200 and r.json()["total_value_usd"] > 0
    r = client.post("/advisor/review", json={"objectives": {"single_stock_sleeve_cap": 0.4}})
    assert r.status_code == 200
    review = r.json()["review"]
    assert len(review["recommendations"]) == 4
    assert client.get("/advisor/reviews").json()["reviews"][0]["id"] == review["id"]
    assert client.get(f"/advisor/reviews/{review['id']}").json()["review"]["recommendations"]
    assert client.get("/advisor/reviews/nope").status_code == 404
    rec_id = review["recommendations"][0]["id"]
    r = client.post(f"/advisor/recommendations/{rec_id}/decision", json={"status": "rejected", "note": "no"})
    assert r.json()["recommendation"]["status"] == "rejected"
    assert client.get("/advisor/recommendations", params={"status": "open"}).json()["recommendations"]
    assert client.get("/advisor/recommendations", params={"status": "bogus"}).status_code == 422
    assert "hypothetical_book" not in review and "hypothetical_book" not in client.get(f"/advisor/reviews/{review['id']}").json()["review"]
    perf = client.get("/advisor/performance").json()
    assert perf["scorecard"]["reviews"] == 1 and perf["reviews"][0]["status"] == "ok"
    assert client.get("/advisor/performance", params={"review_id": "nope"}).status_code == 404
    assert client.post("/advisor/holdings", json={"accounts": []}).status_code == 422


def test_advisor_routes_registered_on_real_app(tmp_path, monkeypatch):
    """The routes are mounted on the shipped FastAPI app and honour loopback dev auth."""
    import api_server

    svc = AdvisorService(AdvisorStore(tmp_path / "advisor.sqlite3"), price_fetcher=fake_fetch,
                         llm_factory=lambda: FakeLLM([json.dumps(REVIEW_JSON)]), now=lambda: NOW)
    monkeypatch.setattr(advisor_routes, "_service", svc)
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    monkeypatch.setattr(api_server, "_API_KEY", "")
    client = TestClient(api_server.app, client=("127.0.0.1", 50000))
    assert client.post("/advisor/holdings", json=HOLDINGS).status_code == 200
    assert client.post("/advisor/review", json={}).status_code == 200
    remote = TestClient(api_server.app, client=("10.0.0.9", 50000))
    assert remote.get("/advisor/reviews").status_code == 403
