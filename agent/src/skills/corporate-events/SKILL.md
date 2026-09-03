---
name: corporate-events
description: Analyze corporate event-driven trades including merger arbitrage spread calculation, insider buying and selling signals from Form 4 filings, equity-compensation interpretation, secondary offering and buyback impact assessment, and delisting or going-concern risk warnings; use when evaluating an announced corporate action or building an event-driven strategy.
category: flow
---

# Corporate Event-Driven Analysis

## Overview

Build event-driven trading strategies around major company-level events (M&A, insider transactions, equity compensation, secondary offerings and buybacks, etc.). Core logic: event announcements contain incremental information, the market takes time to digest it, and systematic excess returns exist around the event date.

Use cases:
- Merger arbitrage (tender offers / definitive mergers / spin-offs)
- Extracting signals from insider and major-holder transactions (Form 4, 13D/13G)
- Analyzing exercise prices and vesting conditions of equity-compensation plans
- Discount arbitrage in secondary offerings / PIPEs / convertible or exchangeable notes
- Avoiding or speculating on delisting and going-concern warnings

## Core Concepts

### Merger Arbitrage

**Deal types in the US market**:
| Type | Frequency | Excess return | Risk |
|------|------|----------|------|
| Reverse merger / SPAC | Low (declined after 2021) | High (30-100%) | Very high (deal failure) |
| Asset acquisition / carve-in | Medium | Medium (10-30%) | High (valuation / regulatory) |
| Stock-for-stock merger | Medium | Low (5-15%) | Low (definitive agreement signed) |
| Cash tender offer | Medium | Low (3-8%) | Lowest |

**Spread calculation**:
```
Merger arbitrage spread = (offer price - current price) / current price
Annualized return = spread / expected time to close (years)

Example:
  Company A launches a tender offer for Company B at $25; B currently trades at $23.50
  Spread = (25 - 23.5) / 23.5 = 6.38%
  Expected close in 3 months, annualized = 6.38% × 4 = 25.5%

Risk assessment:
  Regulatory certainty: HSR clearance received / no FTC-DOJ second request / CFIUS cleared → high certainty
  Consideration: cash > stock + cash > all-stock (decreasing certainty)
  Deal terms: MAC clause (material adverse change), reverse termination fee, financing condition
```

**US merger-arbitrage key points**:
- Deals are announced via press release and Form 8-K with no trading halt, so the initial gap is priced within minutes
- Watch the sequence "exploring strategic alternatives" → definitive agreement (8-K) → proxy / tender documents → close
- Approval chain: board → shareholder vote → antitrust (HSR / FTC / DOJ) → CFIUS for foreign buyers (each step is a risk point)

### Spin-offs

```
US spin-off mechanics:
  - Form 10 registration filed with the SEC; typically structured as tax-free under IRC Section 355
  - The distributed business must generally have an active trade or business history of ≥ 5 years
  - Shareholders receive subsidiary shares pro rata on the distribution date

Trading strategy:
  Announcement → buy the parent (spin-off expectation drives a sum-of-the-parts re-rating)
  Distribution date → index funds often force-sell the SpinCo in the first 1-3 months; trim the parent once the catalyst is realized

Example:
  In 2023 an industrial conglomerate spun off a subsidiary
  Parent +18% in the 20 days after the announcement
  Parent pulled back 8% after the subsidiary's first trading day
```

### Insider Buying and Selling Signals (Form 4)

**Buying signals** (bullish):
| Signal strength | Condition | Excess return (20-day) |
|----------|------|----------------|
| Strong | Controlling holder / 10% owner buys > 1% of shares outstanding, or CEO/CFO open-market buy > $1M | +8~12% |
| Medium | Cluster buying by ≥ 3 insiders | +5~8% |
| Weak | Single director buy | +2~4% |

**Selling signals** (bearish):
| Signal strength | Condition | Excess return (20-day) |
|----------|------|----------------|
| Strong | Controlling holder plans to sell > 2% of shares outstanding (e.g., via a secondary offering) | -5~10% |
| Medium | First sale after IPO lock-up expiry | -3~6% |
| Weak | Departing executive sells | -2~4% |

```
Key windows:
  - 6 months before announcement: insider-trading hot zone; abnormal volume may be informed money
  - 3 days after filing: maximum information shock (Form 4 must be filed within 2 business days)
  - 20 days after filing: excess return largely digested

Filter rules:
  Exclude: pre-scheduled Rule 10b5-1 plan sales, option exercise-and-sell, tax-withholding sales, margin-call liquidations
  Keep: discretionary open-market trades (genuine signal), a sale shortly after a buy (reversal signal)
```

### Equity-Compensation Interpretation

```
Key elements:
  1. Exercise / grant price: discount to the current stock price
     Discount > 50% → strong incentive but heavy dilution
     Discount < 20% (at-the-money is the US norm) → management confident in the stock

  2. Vesting conditions: are the performance targets challenging?
     e.g., PSUs vesting on "3-year net income CAGR ≥ 20%"
     vs industry average growth of 10% → demanding target → positive signal

  3. Recipients: share going to core technical / non-executive staff
     Non-C-suite share > 50% → binds key talent → positive
     Purely C-suite → possible self-dealing

  4. Share source:
     Newly issued shares → dilutes EPS
     Repurchased (treasury) shares → no dilution, more positive

  5. Cliff / vesting period:
     1-year cliff + 3-year vesting → standard plan
     Short cliff + weak conditions → self-dealing suspicion

Empirical reference:
  Average 60-day excess return after plan announcement: +6.2%
  Plans with tougher-than-expected targets: +10.5%
  Exercise price close to the current price: +8.3%
  First-ever plan > repeat plan: higher excess return
```

## Analysis Framework

### 1. Secondary Offerings and Buybacks

**Secondary / follow-on offerings and PIPEs**:
```
Event timeline:
  Shelf registration (S-3) → offering announcement (8-K / press release, usually after the close) → overnight pricing → settlement → lock-up expiry

Trading nodes:
  1. Announcement: focus on the discount and use of proceeds
     Discount = (current price - offer price) / current price
     Modest discount (< 10%) with a strategic or long-only anchor investor → positive (institutions buying = endorsement)
     Steep discount (> 20%) in a PIPE → usually distress-driven, negative

  2. Before pricing: the stock typically drops 3-8% on a dilutive primary offering, less for a sponsor sell-down
     Anchor investors have an incentive to support the stock once their price is locked

  3. Lock-up expiry: PIPE / sponsor shares unlock → selling pressure
     Average decline of 3-5% in the 20 days before expiry
     Pressure continues for 20 days after

Use-of-proceeds scoring:
  Acquiring quality assets: +3
  Capacity expansion / new projects: +2
  General working capital: 0 (neutral to slightly negative)
  Debt repayment: -1
  Insider / major-holder participation > 50%: +2 (aligned interests)

Share buybacks (the positive mirror image):
  Authorization (8-K / press release) is not execution; track actual repurchases in the 10-Q
  Buyback yield = trailing repurchases / market cap; > 3% → meaningful
  Accelerated share repurchase (ASR) → immediate execution, strongest signal
  Buyback + insider buying + dividend raise → strong combined signal; debt-funded buybacks at high leverage → discount the signal
```

**Convertible and exchangeable notes**:
```
Exchangeable note = bond issued by a major shareholder secured by its stake; convertible note = issued by the company itself
  Conversion price = the price agreed at issuance
  When stock > conversion price × 130% → holders convert → equivalent to a shareholder sale / dilution
  When stock < conversion price × 70%  → holders keep the bond → the issuer gets low-rate financing

Trading signals:
  An exchangeable-note issuance = the holder may plan to reduce its stake, but more gradually than an open-market sale
  Near the conversion window with the stock close to the conversion price → watch whether the issuer wants the stock above the conversion price
```

### 2. Delisting and Going-Concern Warnings

**Exchange listing standards (NYSE / Nasdaq)**:
```
Deficiency notices (the US analogue of a risk-warning flag):
  - Closing bid < $1.00 for 30 consecutive trading days → notice, 180-day cure period (Nasdaq may grant a second 180 days)
  - Market value of publicly held shares below the exchange minimum ($15M Nasdaq; NYSE 30-day average market cap < $15M)
  - Stockholders' equity below the minimum (e.g., $2.5M on the Nasdaq Capital Market)
  - Late 10-K / 10-Q (NT filing) → delinquency notice

Audit and control red flags:
  - Going-concern paragraph (substantial doubt) in the auditor's report
  - Adverse opinion / disclaimer of opinion; material weakness under SOX 404
  - Restatement, SEC investigation, or accounting fraud

Delisting triggers:
  - Failure to cure the bid-price deficiency (reverse splits are commonly used to regain compliance)
  - Chapter 11 filing → usually delisted and moved to OTC (Pink / Expert Market)
  - Repeated delinquent filings
```

**Trading strategies**:
```
Avoidance strategy (recommended):
  - Exclude every name with an active deficiency notice or going-concern qualification
  - Exclude potential candidates: "loss in the latest quarter + revenue decline > 30%"
  - Exclude companies whose auditor issued a qualified opinion or resigned

Speculative strategy (high risk, research only):
  Compliance-regained plays: a distressed company returns to profitability → cures the deficiency → re-rating
  Screening conditions:
    - Profitable in the latest quarter (turnaround inflection)
    - Substantive restructuring / debt-exchange plan in place
    - Market cap > $50M (well above the delisting threshold)
  Risk control: position < 5%, stop loss -15%
```

### 3. Event Calendar and Trading Windows

```
T-30 to T-1 (pre-event window):
  Buyback authorization / insider buying → scale in gradually
  Merger announcement → assess certainty, then build the position

T (announcement day):
  Positive event → buy at the open (no daily price limit in the US, so the pre-market gap can fully price the news)
  Negative event → sell in the pre-market or at the open

T+1 to T+20 (post-event window):
  Information is gradually digested and excess return decays
  Large events (M&A / restructuring): digestion can take up to 60 days
  Small events (insider buys / buybacks): mostly digested in 20 days

T+N (long-term effects):
  Around equity-compensation vesting dates: management has an incentive to support the stock
  Lock-up expiry dates: predictable selling pressure
```

## Output Format

Event-driven analysis report:
```
=== Event Overview ===
Ticker: KEY.US KeyCorp
Event: cluster of insider open-market purchases (Form 4, 3 executives)
Date: 2026-03-25
Size: $10-20M (0.8%-1.6% of shares outstanding)

=== Signal Assessment ===
Signal strength: strong (senior insiders + large size)
Historical reference: comparable events average +8.2% 20-day excess return
Certainty: high (filed Form 4 purchases, not a plan announcement)

=== Strategy Recommendation ===
Action: open position at the next day's open
Size: 5-8% (per-event cap)
Holding period: 20-30 trading days
Stop loss: -5% (5% below the announcement-day close)
Take profit: +12% or at the end of the holding period

=== Risks ===
- A market-wide sell-off could offset the event effect
- Follow-on buying could stall → monitor subsequent Form 4 filings
- Bank-sector valuation overhang → excess return may be smaller
```

## Notes

1. **Information timeliness**: US filings appear first on SEC EDGAR (8-K, Form 4, 13D); third-party aggregators lag, and the arbitrage window may already be closed
2. **Insider-trading risk**: abnormal price/volume ahead of an announcement may reflect insider trading; piggybacking is risky (regulatory investigations)
3. **Event clustering**: overlapping events on the same name reinforce the signal (insider buying + buyback + equity plan = strong signal), but rule out a coordinated "defend the stock" package
4. **SPAC / reverse-merger decline**: after the 2021 SPAC bust, shell-company arbitrage has shrunk substantially
5. **Data availability**: SEC EDGAR full-text search and Form 4 feeds are free; commercial APIs add structured insider / offering / buyback data, but Form 4 itself only has to be filed within 2 business days
6. **Position control**: keep any single event-driven strategy at or below 10%; a failed event (e.g., a blocked merger) can produce a 20%+ drop

## China market notes

- A-share deal types: backdoor listings (less common after registration-based IPO reform, 30-100% returns, very high approval risk), asset injections (10-30%), absorption mergers (5-15%), and tender offers (3-8%). Approval chain: board → shareholder meeting → CSRC (and MOFCOM for foreign buyers). Watch the "planning a major asset restructuring" announcement → trading halt → resumption cycle; the first day after resumption is capped at 20% on ChiNext / STAR
- A-share spin-off conditions: listed ≥ 3 years, subsidiary net income ≥ 10% of the parent's, subsidiary net assets ≤ 30% of the parent's
- Insider filters: exclude passive selling from pledge liquidations and discounted block-trade sales (often a hand-off, not a bearish view); keep open-auction sales; the strongest buy signal is a controlling shareholder buying > 1% of total shares
- Private placements (dingzeng): timeline proposal → shareholder meeting → CSRC approval → issuance → unlock; discount = (current price - floor price) / current price, and a discount > 20% is read as positive (institutions willing to buy = endorsement); placement shares typically fall 3-5% into unlock. Rights issues (peigu) and exchangeable bonds (EB) issued by major holders follow the same discount logic
- ST / *ST rules (2024): *ST for a net loss plus revenue < CNY 300M (main board) / CNY 100M (ChiNext), disclaimer or adverse audit opinion, or fraud; ST for fund misappropriation, illegal guarantees, or an adverse internal-control opinion. Delisting: 20 consecutive days of market cap < CNY 300M (main board) / CNY 500M (ChiNext / STAR) or price < CNY 1, or failing *ST criteria the following year. The "cap removal" play: *ST turns profitable → applies to remove the flag → limit-up run; screen for market cap > CNY 1B
- Data: announcements are first published on exchange websites and cninfo (juchao); tushare provides insider, equity-plan, and placement data with T+1 or slower latency. Use the daily price-limit queue (limit-up order size) when entering at the open auction
- Illustrative A-share output: 000001.SZ Ping An Bank, controlling-shareholder purchase plan of CNY 1-2B (0.8%-1.6% of shares) with a 6-month execution window

## Dependencies

```bash
pip install pandas numpy
```
