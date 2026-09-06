# Advisor API: plugging Vibe-Trading into a personal finance app

Vibe-Trading runs locally as the investment brain. Your finance app pushes
account holdings, asks for a wealth-manager review, records what you did with
each recommendation, and reads back a track record. No order is ever placed.

```
finance app ──POST /advisor/holdings──▶ Vibe-Trading (127.0.0.1:8899)
            ──POST /advisor/review────▶   prices holdings, runs risk x-ray,
            ◀── review + recommendations   one LLM call with a strict JSON schema
            ──POST …/decision─────────▶   you mark accepted / rejected
            ◀── GET /advisor/performance   frozen actual book vs advised book vs SPY
```

## Run it

```bash
pip install "vibe-trading-ai[anthropic]"          # or: pip install -e ".[anthropic]" from this checkout
cp agent/.env.example agent/.env                   # set ANTHROPIC_API_KEY and API_AUTH_KEY
vibe-trading serve --port 8899                     # loopback only by default
```

Prices come from free sources (Yahoo for US stocks and ETFs, OKX for crypto);
no data key is needed. Set `API_AUTH_KEY` and send it as `Authorization: Bearer`
from the app; without it only same-machine calls are accepted.

## Endpoints

All responses are JSON with `"status": "ok"`; errors use HTTP status codes
(404 no holdings or review, 422 invalid body, 502 model returned no usable review).

| Method | Path | Body / query | Returns |
|---|---|---|---|
| POST | `/advisor/holdings` | `HoldingsIn` | valued snapshot: totals, per-account values, combined holdings, allocation, data gaps |
| GET | `/advisor/holdings/latest` | | the raw snapshot last pushed |
| POST | `/advisor/review` | `{snapshot_id?, objectives?}` | the review with priced recommendations (30-120 s) |
| GET | `/advisor/reviews` | `limit` | past reviews, newest first |
| GET | `/advisor/reviews/{id}` | | one review with its recommendations |
| GET | `/advisor/recommendations` | `status`, `review_id` | ledger rows |
| POST | `/advisor/recommendations/{id}/decision` | `{status: accepted\|rejected, note}` | updated row |
| GET | `/advisor/performance` | `review_id?`, `limit` | scorecard plus per-review curves and per-call scoring |

### HoldingsIn

```json
{
  "as_of": "2026-09-06",
  "accounts": [
    {"id": "schwab-taxable", "name": "Schwab Individual", "type": "taxable", "cash_usd": 5000,
     "positions": [{"symbol": "AAPL", "quantity": 50, "cost_basis_usd": 6000},
                   {"symbol": "VTI", "quantity": 40, "asset_class": "etf"}]},
    {"id": "schwab-roth", "name": "Schwab Roth IRA", "type": "roth_ira", "cash_usd": 1000,
     "positions": [{"symbol": "VTI", "quantity": 30, "asset_class": "etf"}]},
    {"id": "fidelity-hsa", "name": "Fidelity HSA", "type": "hsa", "cash_usd": 0,
     "positions": [{"symbol": "FXAIX", "quantity": 20, "asset_class": "etf"}]},
    {"id": "robinhood", "name": "Robinhood", "type": "crypto", "cash_usd": 0,
     "positions": [{"symbol": "BTC", "quantity": 0.1, "asset_class": "crypto"}]}
  ]
}
```

Account types: `taxable`, `roth_ira`, `traditional_ira`, `401k`, `hsa`, `crypto`, `other`.
Symbols are plain tickers. Mark crypto with `asset_class: "crypto"` (major coins
are recognised without it). `USDC`, `USDT`, `DAI` and `asset_class: "cash"` count as cash.
A symbol with no price history is reported in `data_gaps` and excluded from
weights and risk, never silently dropped or guessed.

### Objectives (the mandate the advisor reviews against)

```json
{"risk_tolerance": "aggressive", "horizon_years": 15,
 "single_stock_sleeve_cap": 0.40, "max_position_weight": 0.15,
 "benchmark": "SPY", "notes": "Prefer to add in the Roth; no new crypto."}
```

### What a recommendation looks like

```json
{"id": "rec_1f3c…", "action": "trim", "symbol": "NVDA", "is_new_position": false,
 "resolved_account_id": "schwab-taxable", "amount_usd": 5000, "quantity": 27.4,
 "price_at_rec": 182.31, "confidence": 0.7, "horizon": "years",
 "rationale": "NVDA is 21% of the book against a 15% cap …",
 "tax_note": "Lots are long-term; realises about $3.1k of gains.",
 "status": "open"}
```

`price_at_rec` and `quantity` are set by the server from market data at review
time, never by the model. Sell, trim and hold may only name held symbols;
anything else is dropped and logged.

## How the track record works

Every review freezes two books on its date: your actual holdings and the
"advised" book after applying the recommendations (cash moves with each buy or
sell, so both start at the same value). `GET /advisor/performance` marks both
to market on the same daily closes next to SPY, so `advice_delta_usd` is
exactly what following the advice would have added or cost. Each call is also
scored on its own: a buy or hold is a hit if the symbol beat SPY since the
call, a sell or trim if it lagged. Holds are scored the same way but shown
only per action; the headline hit rate and average excess return count
buys, sells and trims across reviews. Decisions you record (`accepted` / `rejected`) do not
change the scoring; they let you compare the agent's record with your own.

## Finance-app side

`integrations/finance-app/advisorClient.ts` is a dependency-free TypeScript
client and `InvestmentsSection.tsx` a plain React section that pushes
holdings, runs a review, lists open calls with accept / skip buttons, and shows
the scorecard and per-review curves. Wire `loadHoldings` to your aggregator's
positions endpoint and you have the Investments tab.

Storage is `~/.vibe-trading/advisor/advisor.sqlite3`. Nothing in the advisor
touches the trading connectors, mandates, or order tools.
