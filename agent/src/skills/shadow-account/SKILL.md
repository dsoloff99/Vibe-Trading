---
name: shadow-account
description: "Shadow Account distills a user's own trade journal into 3-5 plain-language profit rules, backtests them across US / HK / A-share / crypto markets, attributes the gap between real and shadow PnL, and renders an 8-section PDF report; use it when the user asks to extract their strategy, train their shadow, backtest their own playbook, or find out how much more they could have made."
category: analysis
---

# Shadow Account

## When to Trigger

Load this skill when the user says "extract my strategy" / "train my shadow" / "backtest my playbook" / "how much more could I have made" / "what is my profit pattern".

**Prerequisite**: the user has uploaded a trade journal (broker export from Tonghuashun / Eastmoney / Futu, or a generic CSV such as Schwab, Fidelity, IBKR, Robinhood exports) and `analyze_trade_journal` has already been run. If not, run the Phase 4a tool first.

## Workflow (four steps)

1. `extract_shadow_strategy(journal_path=...)`
   - Returns a `shadow_id` plus 3-5 plain-language rules
   - Confirm with the user: "Do these rules sound like you?" If the user says no, raise `min_support` and rerun
2. `run_shadow_backtest(shadow_id=..., journal_path=...)`
   - Returns per-market metrics, `delta_pnl`, and the attribution breakdown
   - Runs all four markets by default (china_a/hk/us/crypto)
3. `render_shadow_report(shadow_id=...)`
   - Generates HTML + PDF (falls back to HTML-only automatically if weasyprint fails)
   - Returns `html_path` / `pdf_path` / `delta_pnl`
4. (Optional) `scan_shadow_signals(shadow_id=...)` — list of symbols that fall inside the shadow's entry window today (research only)

## Interpreting the Output

### Rule Cards
Each rule contains `rule_id`, `human_text` (<= 80 characters), `support_count`, `coverage_rate`, `holding_days_range`. A rule is not a "guaranteed-profit formula"; it is a "portrait of what the user's profitable trades have in common".

### Backtest Matrix
- `per_market`: Sharpe / annualized return / max drawdown for each of the four markets
- `combined`: performance of the merged pool
- `equity_curve`: equity time series (goes into PDF Section 3)

### Gap Attribution (PDF Section 5 — the gut punch)
All values are signed; positive = the shadow earned more than the user:
- `noise_trades_pnl`: cumulative PnL of real trades that match no rule (the user's emotional trades)
- `early_exit_pnl`: winners held shorter than the rule's lower bound, opportunity cost prorated by the shortfall
- `late_exit_pnl`: losers held longer than the rule's upper bound, amplified loss prorated by the overrun
- `overtrading_pnl`: PnL of real trades beyond the rule's frequency limit
- `missed_signals_pnl`: residual (shadow_pnl - real_pnl - sum of the four items above)

### Counterfactual Top 5
Sorted by `|impact|`, lists the 5 trades that "should have been taken but weren't / should not have been taken but were", with specific dates and reasons.

## Conversation Templates

**Confirming the rules**:
> From your {profitable_roundtrips} profitable round trips I extracted these rules: {rules}. Do these look like your own playbook?

**Presenting the gap** (Section 5):
> Shadow PnL **{shadow_pnl:+.0f}** / your real PnL **{real_pnl:+.0f}** / gap **{delta_pnl:+.0f}**. Of that, **{noise_trades_pnl:+.0f}** came from "emotional trades" that match none of your profit rules.

**Today's scan** (disclaimer is mandatory):
> Symbols inside your shadow's entry rhythm today: {symbols}. **Research only, not a buy recommendation.**

## Rule Translation Prompt Template

When `extract_shadow_strategy` is called, an `llm_translator` callable can be injected to translate the structured entry_condition into natural language:

```
[Context] Among a retail trader's profitable round trips, {N} trades share the same conditions:
  market = {market}
  entry_hour in [{hour_min}, {hour_max}]
  held for {hold_lo}-{hold_hi} days
[Task] Write one rule of <= 80 characters in plain English, in the voice of the trader describing their own habit, without jargon.
[Output] Return only the one-line rule text, no explanation.
```

Without an injected translator, the f-string template is used (see `extractor._translate_rule`).

## Red Lines

- **No order placement**: these tools never connect to any order-routing channel; research output only
- **No copying other people's strategies**: Shadow Account is the user's own shadow; it never extracts rules from community or public strategies
- **Insufficient samples must raise**: profitable roundtrips < 5 -> raise immediately, never fabricate
