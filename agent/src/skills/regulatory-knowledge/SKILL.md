---
name: regulatory-knowledge
description: Reference for trading rules and regulation across US, Hong Kong, China A-share and crypto markets (PDT rule, circuit breakers, T+1 settlement, wash-sale rule, Reg T margin, SEC/FINRA, IRS capital gains, price limits, short-selling, stamp duties); use it when implementing backtest constraints, checking a strategy for compliance, or estimating trading costs and tax drag.
category: tool
---

# Market Regulation Knowledge Base

## Overview

Trading rules every quantitative trader must understand, market by market. Wrong assumptions about trading rules produce distorted backtests (e.g. ignoring A-share price limits), live-trading violations (e.g. tripping the US PDT rule), or avoidable tax losses (e.g. wash sales).

Use cases:
- Implementing trading-rule constraints correctly in a backtest engine
- Handling rule differences in cross-market strategies
- Setting compliance and risk-control parameters
- Folding tax impact into strategy return calculations

## Core Concepts

### US Trading Rules

**Trading hours (Eastern Time)**:
```
Regular session: 9:30-16:00 ET
Pre-market: 4:00-9:30 ET (most retail brokers open access from 7:00 or 8:00)
After-hours: 16:00-20:00 ET
Regulators: SEC (markets, issuers, advisers), FINRA (broker-dealers, margin and PDT rules),
            CFTC (futures and most crypto derivatives)

Backtest impact:
  - Extended-hours volume is thin and spreads are wide; do not fill at pre/after-hours prints
  - Daily bars use the 9:30 opening auction and the 16:00 closing auction prints
```

**PDT rule (Pattern Day Trader, FINRA Rule 4210)**:
```
Trigger: >= 4 day trades (open and close the same day) within 5 business days in a margin account,
         when those day trades exceed 6% of total trades in that window
Once flagged: the account must hold >= $25,000 equity to keep day trading
Below $25,000: 90-day restriction to closing-only trades (or until equity is restored)

Ways to stay compliant:
  - Use a cash account (no PDT rule, but only settled funds can be reused; free-riding rules apply)
  - Keep account equity > $25,000
  - Keep day-trade frequency < 4 per rolling 5 business days
```

**Settlement (T+1)**:
```
US equities, ETFs and corporate bonds settle T+1 (since May 28, 2024); listed options already settled T+1
Margin account: buy and sell the same day on margin (each round trip counts toward PDT)
Cash account: sale proceeds can fund a new purchase immediately, but selling that new position
              before the original sale settles is a "good faith violation";
              3 violations in 12 months -> 90-day settled-cash-only restriction

Backtest impact: T+1 affects cash-account capital recycling, not signal timing
```

**Reg T margin (Federal Reserve Regulation T)**:
```
Initial margin: 50% (max 2x leverage on long equity purchases)
Maintenance margin: 25% FINRA minimum (most brokers require 30-40%, more on volatile names)
Below maintenance: margin call -> deposit funds or the broker liquidates positions
Short sales: 150% of proceeds must be held (100% proceeds + 50% initial margin)
Portfolio margin: risk-based, up to about 6x, requires roughly $100,000-125,000 equity and approval

Backtest impact:
  - Cap gross exposure at 2x for a Reg T account; charge margin interest (broker rate ~ Fed funds + 1-6%)
  - Model forced liquidation at the maintenance threshold, not the initial threshold
```

**Wash-sale rule (IRS Section 1091)**:
```
Selling a security at a loss and buying a "substantially identical" security within 30 days
before or after the sale -> the loss is disallowed and added to the cost basis of the
replacement shares. Applies across all of your accounts (including IRAs and a spouse's accounts).

Backtest impact:
  - High-turnover strategies that re-enter the same ticker within 30 days lose the current-year
    tax benefit of their losses (deferred, not eliminated)
  - Mean-reversion strategies on the same names are most exposed; track a 61-day window per symbol
```

**Circuit breakers**:
```
Market-wide (S&P 500 vs prior close):
  Level 1: -7%  -> 15-minute halt (not triggered after 15:25 ET)
  Level 2: -13% -> 15-minute halt (not triggered after 15:25 ET)
  Level 3: -20% -> trading halted for the rest of the day

Single-stock LULD (Limit Up-Limit Down):
  Price moves outside +/-5% (Tier 1: S&P 500 / Russell 1000 / active ETPs) or +/-10% (Tier 2)
  of a 5-minute reference price -> 5-minute halt; bands double in the last 25 minutes

Reg SHO (short-selling rules):
  - Locate requirement: must confirm shares can be borrowed before shorting
  - Close-out: fails to deliver must be closed out (T+4 for most, T+6 for market makers)
  - Short Sale Circuit Breaker (Rule 201): stock down >10% from prior close -> uptick-only
    shorting for the rest of that day and the following day

Backtest impact:
  - No daily price limits in US equities, but LULD halts can delay stop-loss fills
  - Same-day round trips are allowed in a margin account -> intraday strategies are feasible
  - Model extended-hours fills with extra slippage or skip them entirely
```

### Hong Kong Trading Rules

```
Trading hours (HKT):
  Pre-opening auction: 9:00-9:30
  Continuous trading: 9:30-12:00, 13:00-16:00
  Closing auction: 16:00-16:10

Key differences (vs US):
  ✓ T+0 trading (buy and sell the same day; no PDT rule)
  ✓ No daily price limits (a single stock can move 50%+ in a day)
  ✓ Established short-selling framework (borrow cost about 1-3%/year on large caps)
  ✓ Grey-market trading (the evening before an IPO lists)
  ✗ Lower liquidity (daily turnover roughly 1/5 to 1/10 of the A-share market)
  ✗ Many penny stocks (large numbers of names trading below HK$0.10)

Short-selling rules:
  - Only designated securities can be shorted, and only at or above the best ask (an uptick-rule variant)
  - Shares must be borrowed before shorting (naked shorting is prohibited)
  - Short positions must be reported when they reach the 0.02% threshold

Settlement:
  T+2 settlement (shares withdrawable on T+2)
  Trading is T+0 (under the pre-funding model)

Backtest impact:
  - No price limits -> extreme moves are common; stop-losses matter more
  - T+0 -> intraday strategies are feasible
  - Low liquidity -> large slippage on small caps; include market-impact cost
```

### China A-share Trading Rules

**Daily price limits**:
| Board | Daily limit | IPO first day | ST stocks |
|------|--------|----------|----------|
| Main board (SSE/SZSE) | ±10% | +44%/-36% | ±5% |
| ChiNext | ±20% | No limit for first 5 days | ±20% |
| STAR Market | ±20% | No limit for first 5 days | ±20% |
| Beijing Stock Exchange | ±30% | No limit for first 5 days | ±30% |

```
Backtest impact:
  Buying at limit-up may not fill (order queue locked) -> signal delayed
  Selling at limit-down may not fill (order queue locked) -> stop-loss fails

Backtest implementation:
  if daily_return >= limit_up:
      buy_signal cannot execute; defer to the next day
  if daily_return <= limit_down:
      sell_signal may not execute; simulate the fill at the limit-down price
```

**T+1 rule**:
```
A-shares: bought on day T -> can only be sold on T+1
Backtest impact: signal on T -> buy at the T+1 open -> earliest sale on T+2
Common error: closing a T-day signal on day T in the backtest -> inflated returns

Exceptions:
  - Securities-lending short sales: effectively T+0 (sell borrowed shares, buy back the same day)
  - ETF arbitrage: primary-market creation/redemption allows de facto T+0
  - Convertible bonds: trade T+0
```

**Margin financing / securities lending**:
```
Margin buying (leveraged long):
  Margin ratio: >= 100% (i.e. max 2x leverage)
  Maintenance ratio: >= 130% (margin call below; forced liquidation below 110%)
  Eligible universe: about 1,600 liquid main-board / ChiNext names

Securities lending (short):
  Sources: broker inventory + refinancing (China Securities Finance)
  Cost: 8-10%/year (far above the 1-2% typical in the US)
  Restrictions: T+0 short sales restricted since 2023; borrowable supply tightened sharply

Backtest impact:
  Shorting A-shares is very expensive; deduct 8-10%/year of borrow cost
  Actual borrowable names < theoretical universe (limited supply)
```

**Call auction and continuous trading**:
```
Opening call auction: 9:15-9:25 (orders cancelable 9:15-9:20, not cancelable 9:20-9:25)
  9:25 sets the opening price
Continuous trading: 9:30-11:30, 13:00-14:57
Closing call auction: 14:57-15:00 (no cancellations)

Backtest impact:
  - Daily backtests default to filling at the T+1 open
  - Last 3-minute closing auction: large orders cluster; VWAP strategies must account for it
  - Limit orders placed during the call auction can move the opening price
```

**Block trades**:
```
Time: 15:00-15:30 (after the close)
Discount: typically 3-8% below the closing price
Restriction: the buyer cannot sell in the secondary market for 6 months (used for major-holder reductions)

Signal meaning:
  Frequent block trades + large discount -> likely insider selling pressure (bearish)
  Lock-up ends 6 months after the block -> watch for selling pressure on the unlock date
```

### Crypto Regulation

```
Major jurisdictions (as of 2026):
  United States: SEC/CFTC dual oversight; spot BTC/ETH ETFs approved; exchanges need FinCEN MSB registration and state licenses
  Hong Kong: VASP licensing regime; licensed exchanges (HashKey, etc.)
  Mainland China: exchange operations and ICOs banned, but holding is not illegal
  European Union: MiCA fully in force since 2024
  Japan: FSA supervision; exchanges must register
  Singapore: MAS supervision under the Payment Services Act

Stablecoin regulatory trends:
  - USDT: reserve-transparency disputes; restricted in some jurisdictions
  - USDC: stronger compliance profile; Circle is US-regulated
  - Central-bank digital currencies (CBDCs) may displace some use cases

DeFi compliance:
  - Most DeFi protocols currently sit in a regulatory grey area
  - Trend: front-end KYC required, on-chain transactions remain permissionless
  - Risk: smart-contract losses are not covered by investor-protection law

Backtest impact:
  - Crypto trades 24/7 with no market close
  - No price limits; extreme moves can exceed 50%/day
  - Cross-exchange spreads can reach 1-3% (arbitrage opportunity, but with counterparty risk)
  - Major exchanges (OKX etc.) offer up to 125x on perpetuals; the backtest must compute liquidation prices correctly
  - US taxpayers: every crypto sale or swap is a taxable event (see Tax Impact below)
```

## Analysis Framework

### 1. Backtest Rule-Constraint Matrix

```
| Rule | US | HK | A-share | Crypto (OKX) |
|------|-----|------|------|-----------|
| Price limits | LULD halts | None | ±10/20/30% | None |
| T+N | T+1 settle, same-day trading (margin) | T+0 trading, T+2 settle | T+1 | T+0 |
| Shorting | Easy (locate required) | Easy | Securities lending (expensive) | Perpetual futures |
| Trading hours | 6.5h/day | 5.5h/day | 4h/day | 24/7 |
| Fees | $0 commission (most brokers) + SEC/FINRA fees | 0.03% + 0.1% stamp duty | 0.025% + 0.05% stamp duty | 0.02-0.05% |
| Min trade size | 1 share (fractional at some brokers) | 1 board lot (varies) | 100 shares | 0.001 BTC |
```

### 2. Compliance Checklist for Cross-Market Strategies

```
Checklist:
  □ Do trading hours overlap (time-zone conversion)?
  □ Holiday differences (US Thanksgiving/Christmas vs A-share Lunar New Year/National Day)
  □ Is FX risk included (USD / HKD / CNY / USDT)?
  □ Can short signals actually be executed (borrow availability; A-share restrictions)?
  □ Minimum trade-size constraints (HK board lots; A-share 100-share round lots -> small accounts cannot size precisely)
  □ Are stamp duties, exchange fees and regulatory fees included?
  □ Does the strategy trip the PDT rule or the wash-sale rule in a US account?

US real trading costs (retail):
  Commission: $0 at most brokers (IBKR Pro about $0.005/share, min $1)
  SEC fee: $27.80 per $1M sold (FY2025 rate; sells only)
  FINRA TAF: $0.000166/share sold (max $8.30 per trade)
  Spread + slippage: 0.01-0.05% on large caps, far more on small caps
  Total (round trip): about 0.03-0.1% on liquid names

  Impact: 1 turnover/month -> about 0.4-1.2%/year in explicit + implicit costs
          4 turnovers/month -> about 1.5-5%/year, plus short-term-gains tax drag (see below)

A-share real trading costs:
  Commission: 0.025% (min CNY 5 per order)
  Stamp duty: 0.05% (sells only; halved in 2023)
  Transfer fee: 0.001%
  Regulatory fees: 0.00687%
  Total (one way): about 0.08%
  Total (round trip): about 0.16%
```

### 3. Tax Impact

```
United States (IRS):
  Capital gains: short-term (held <= 1 year) taxed as ordinary income (10-37%);
                 long-term (held > 1 year) at 0/15/20% by income bracket, plus 3.8% NIIT for high earners
  Dividends: qualified dividends taxed at long-term rates (needs > 60 days held around the ex-date);
             non-qualified dividends (REITs, most foreign payers, short holds) taxed as ordinary income
  Losses: offset gains; up to $3,000/year of net losses against ordinary income; the rest carries forward
  Wash sales: disallowed losses are added to basis (see above)
  Section 1256 contracts (index options, futures): 60% long-term / 40% short-term regardless of holding period
  Tax-advantaged accounts (IRA/401k): no capital-gains tax on trades inside the account (but no loss harvesting either)
  Reporting: broker Form 1099-B; cost-basis method FIFO by default, specific-lot if elected

  Backtest impact: a high-turnover strategy pays short-term rates on every gain;
  a 20% gross return nets about 13% at a 35% marginal rate versus about 16% if held > 1 year

Hong Kong:
  Capital gains: none
  Dividend tax: none for HK-domiciled companies (US holders still owe US tax on the dividends)
  Stamp duty: 0.1% per side is the main friction

China A-share (mainland residents):
  Stock trading gains: exempt from individual income tax (exemption extended through 2024 and beyond)
  Dividend tax: exempt if held > 1 year; 10% for 1 month-1 year; 20% if held < 1 month
  Fund distributions: exempt
  US holders (via Stock Connect or ADRs): 10% withholding under the US-China treaty, creditable on Form 1116

Crypto:
  United States: taxed as property; every sale, swap, or spend is a capital-gains event
                 (short/long-term rates as above); staking and mining rewards are ordinary income;
                 the wash-sale rule does not currently apply to crypto; broker 1099-DA reporting from 2025
  Mainland China: no explicit tax rules yet (large transactions may be traced retroactively)

  Backtest impact: once tax is included, the net return of frequent-trading strategies drops significantly
```

## Output Format

Compliance check report:
```
=== Strategy Compliance Check ===
Strategy: US + HK long/short cross-listing pair trade
Instruments: BABA (Alibaba ADR, NYSE) + 9988.HK (Alibaba, HKEX)

=== Rule Constraints ===
US short: locate required -> BABA borrow cost about 0.5%/year, ample supply
HK short: 9988.HK is a designated short-sell security; borrow cost about 1.5%/year
PDT: same-day round trips on the US leg count as day trades -> keep equity > $25,000 or hold overnight
Settlement: US T+1 vs HK T+2 -> cash-account users must track settled funds separately
Price limits: none on either leg, but an LULD halt on BABA can delay one side of the pair
Trading hours: HK 9:30-16:00 HKT vs US 9:30-16:00 ET -> no overlap; each leg is exposed alone for about 17 hours
Wash sale: BABA and 9988.HK are likely "substantially identical" -> a loss on one leg can be disallowed if the other is bought within 30 days

=== Cost Estimate ===
US trading cost: about 0.05%/round trip (spread + SEC/FINRA fees)
HK trading cost: 0.26%/round trip (incl. 0.1% stamp duty)
Borrow cost (US): 0.5%/year
Borrow cost (HK): 1.5%/year
FX hedging cost: near zero (HKD is pegged to USD)

=== Recommendations ===
1. Hold each leg overnight instead of round-tripping intraday -> avoids PDT day-trade counts
2. Execute the HK leg at the HK close and the US leg at the US open; size for the overnight gap
3. Track the 61-day wash-sale window on both tickers; consider running the pair inside an IRA if allowed
```

## Notes

1. **Rules change constantly**: regulators adjust rules frequently (US T+1 settlement in 2024, A-share stamp-duty cut in 2023, securities-lending restrictions); backtests should apply the rules in force at each historical point
2. **Backtest vs live gap**: unfillable orders at halts and price limits are the largest source of backtest distortion; high-turnover strategies must model them strictly
3. **Special sessions**: US opening/closing auctions and A-share call auctions (9:15-9:25 and 14:57-15:00) behave differently from continuous trading; signal execution must distinguish them
4. **Cross-market holidays**: the A-share Lunar New Year closure lasts about 10 days while HK, US and crypto keep trading; handle the signal gap
5. **Regulatory risk premium**: policy uncertainty in crypto is itself a risk factor and should be built into the strategy
6. **Broker differences**: commissions, borrow rates, margin rates and system latency vary widely between brokers; use conservative backtest parameters

## Dependencies

```bash
pip install pandas numpy
```
