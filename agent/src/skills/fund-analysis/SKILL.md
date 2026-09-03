---
name: fund-analysis
description: Analyze and screen mutual funds and ETFs using Morningstar ratings, Sharpe and information ratios, Sharpe style-box regression, style-drift detection, manager evaluation, ETF selection criteria, and fund-of-funds portfolio construction; use when evaluating, comparing, or selecting funds or building a multi-fund portfolio.
category: asset-class
---

# Fund Analysis and Screening

## Overview

Systematically evaluate the performance, investment style, and management quality of mutual funds, hedge funds, and ETFs, and build fund-of-funds (FOF) portfolios. Core objective: find "sustainable sources of excess return" rather than "the fund with the best past performance".

Use cases:
- Multi-dimensional screening of equity and allocation (balanced) funds
- Attribution of a fund manager's investment style and detection of style drift
- Tracking-efficiency evaluation of ETF products
- Asset allocation and rebalancing of a fund-of-funds portfolio
- Market-specific analysis dimensions for China A-share mutual funds (see China market notes)

## Core Concepts

### Fund Performance Metrics

**Return metrics**:
| Metric | Formula | Good threshold | Notes |
|------|------|----------|------|
| Annualized return | (1+total return)^(1/years)-1 | > 15% (equity funds) | Absolute return |
| Excess return (Alpha) | Fund return - benchmark return | > 5%/yr | Relative to benchmark |
| Information ratio (IR) | Alpha / tracking error | > 0.5 | Alpha consistency |
| Hit rate | Share of months beating the benchmark | > 55% | Consistency |

**Risk metrics**:
| Metric | Formula | Good threshold | Notes |
|------|------|----------|------|
| Max drawdown | max(peak-trough)/peak | < 20% (equity funds) | Tail risk |
| Annualized volatility | std(daily returns)*√252 | < 20% (equity funds) | Total risk |
| Downside deviation | std(negative returns)*√252 | < 13% | Downside risk |
| Calmar ratio | Annualized return / max drawdown | > 1.0 | Return per unit of tail risk |

**Risk-adjusted metrics**:
| Metric | Formula | Good threshold | Notes |
|------|------|----------|------|
| Sharpe ratio | (Rp-Rf)/σp | > 1.0 | Return per unit of total risk |
| Sortino ratio | (Rp-Rf)/downside σ | > 1.5 | Focuses on downside risk |
| Treynor ratio | (Rp-Rf)/β | > 10% | Return per unit of systematic risk |

```
Risk-free rate (Rf): US convention is the 3-month T-bill yield (or 1-year Treasury), roughly 4-5% in the current cycle
Benchmark: equity funds → S&P 500 (SPY); allocation funds → 60% S&P 500 + 40% Bloomberg US Aggregate Bond (AGG)
Evaluation window: at least 3 years, 5 years preferred (covers a full bull/bear cycle)
```

### Sharpe Style-Box Analysis

**Nine-box style classification**:
```
            Value        Blend        Growth
Large    Large Value   Large Blend   Large Growth
Mid      Mid Value     Mid Blend     Mid Growth
Small    Small Value   Small Blend   Small Growth

Determination method (returns-based regression):
  Ri = α + β1×Large Value + β2×Large Growth + β3×Small Value + β4×Small Growth + ε

  Style index selection (US):
  Large Value:  Russell 1000 Value (IWD)
  Large Growth: Russell 1000 Growth (IWF)
  Small Value:  Russell 2000 Value (IWN)
  Small Growth: Russell 2000 Growth (IWO)

  Direction with the largest β weight = the fund's primary style
  R² > 0.85 → clear style; R² < 0.70 → ambiguous style / market-timing fund
```

### Style-Drift Detection

```
Method: rolling-window regression (window = 60 trading days, step = 20 days)

Drift criteria:
  1. Compute the style weights β for each window
  2. Change in β between adjacent windows:
     |Δβ| > 0.2 → significant drift
     The style with the largest β changed → style switch

  3. R² time series:
     R² steadily declining → manager is timing / deviating from the benchmark
     R² swinging up and down → unstable style

Drift types:
  - Gradual drift: large → mid → small cap (usually forced down-cap after asset growth)
  - Abrupt drift: value suddenly switches to growth (possibly a manager change)
  - Cyclical drift: chases growth in bull markets, rotates to value in bear markets (timing fund)

Common US drift pattern:
  2020-2021: many self-described "value" funds drifted holdings toward mega-cap tech / software (growth)
  Detection: stated style = Large Value, regressed style = Large Growth → mislabeled fund
```

## Analysis Framework

### 1. Fund Screening Framework (Five Steps)

```
Step 1: Hard filters
  □ Inception ≥ 3 years
  □ AUM $200M-$20B (too small = liquidation/merger risk, too large = hard to maneuver)
  □ Same manager in place ≥ 2 years
  □ Institutional ownership > 20% (institutional endorsement)

Step 2: Performance ranking
  □ 3-year annualized return > Morningstar category median
  □ 3-year Sharpe ratio > top 30% of category
  □ Max drawdown < category median
  □ Information ratio > 0.3

Step 3: Style verification
  □ Actual style matches stated style (R² > 0.8)
  □ Style-drift score < 0.3 (stable)
  □ 1-year style consistent with 3-year style

Step 4: Manager evaluation
  □ Has managed funds in the same category ≥ 3 years
  □ Positive excess return across every previously managed fund
  □ Reasonable turnover (annualized 30-100% is typical; >200% is high)
  □ Moderate concentration (top 10 holdings 30-60%)

Step 5: Fee check
  □ Expense ratio ≤ 1.0% (active equity funds)
  □ No front-end load and no punitive redemption fee (or a no-load share class is available)
  □ 12b-1 fee ≤ 0.25%
```

### 2. Fund Manager Evaluation

```
Core dimensions:
  1. Excess-return ability:
     Annualized Alpha over tenure (vs. benchmark)
     Bull-market Alpha vs. bear-market Alpha (great managers add value in bear markets too)

  2. Risk control:
     Max drawdown vs. benchmark max drawdown
     Downside capture ratio < 0.8 → good at limiting downside
     Upside capture ratio > 1.0 → keeps pace in rallies

  3. Stock selection vs. market timing (Treynor-Mazuy model):
     Ri-Rf = α + β(Rm-Rf) + γ(Rm-Rf)² + ε
     α > 0 → stock-selection skill
     γ > 0 → market-timing skill
     Empirical evidence: most managers show some selection skill, very few show timing skill

  4. Holding characteristics:
     Turnover: <30% = long-term holder; 30-100% = moderate; >200% = frequent trading
     Concentration: top-10 weight, >60% = concentrated, <30% = diversified
     Sector deviation: over/underweight vs. benchmark GICS sectors

Manager-change signals:
  From the manager-change announcement date:
  - New manager from the same firm with a similar style → limited impact
  - New manager with a very different style → re-evaluate, observe 1-2 quarters before deciding
  - Star manager departs → consider redeeming, track the new manager's other products
```

### 3. ETF Selection Framework

```
Core criteria:
  1. Tracking error: annualized < 2% (passive) / < 4% (enhanced or active)
     Calculation: std(ETF daily return - index daily return) × √252

  2. Fee comparison:
     Expense ratio: 0.03% (lowest) ~ 0.50% (typical)
     A 0.2%/yr fee gap compounds into a meaningful difference over 10 years

  3. Liquidity:
     Average daily dollar volume > $50M → ample liquidity
     Bid-ask spread < 0.1% → low trading cost
     Premium/discount to NAV < 0.3% → accurate pricing

  4. Size:
     > $1B AUM → negligible closure risk
     $200M-$1B → acceptable
     < $200M → check for closure risk

Major US broad-market ETF comparison (example):
  | ETF | Ticker | Expense ratio | AUM | Tracking error |
  |-----|------|------|------|----------|
  | SPDR S&P 500 ETF | SPY | 0.09% | $500B+ | 0.05% |
  | Vanguard S&P 500 ETF | VOO | 0.03% | $400B+ | 0.03% |
  | Invesco QQQ (Nasdaq-100) | QQQ | 0.20% | $250B+ | 0.10% |
  | iShares Russell 2000 ETF | IWM | 0.19% | $60B+ | 0.15% |
```

### 4. Fund-of-Funds Portfolio Construction

```
Step 1: Strategic asset allocation
  Conservative: equity funds 30% + bond funds 50% + money market 20%
  Balanced:     equity funds 50% + bond funds 30% + commodities 10% + money market 10%
  Aggressive:   equity funds 70% + bond funds 20% + commodities 10%

Step 2: Fund selection within each sleeve
  Pick 2-3 funds per asset class (diversify manager risk)

  Equity sleeve:
    1 large value + 1 large growth + 1 small/mid cap
    Complementary styles reduce single-style exposure

  Bond sleeve:
    1 core investment-grade bond fund + 1 convertible or multi-sector fund
    Control credit risk, do not chase high-yield

Step 3: Rebalancing rules
  Scheduled: check deviation once per quarter
  Trigger: any sleeve deviates from target weight by > 5% → rebalance

  Rebalancing methods:
    a. Sell overweight, buy underweight → highest trading cost (and taxable gains in a brokerage account)
    b. Direct new contributions to underweight sleeves → fewer trades
    c. Reinvest distributions into underweight sleeves → best option

Step 4: Monitoring and alerts
  □ Quarterly performance review: any fund in the bottom 30% of its category for 2 consecutive quarters → watch list
  □ Manager change → re-evaluate
  □ Style drift → replace with a style-consistent peer
  □ Abnormal AUM change (surge/collapse) → watch for liquidity impact
```

## Output Format

Fund analysis report:
```
=== Fund Overview ===
Name: Fidelity Contrafund (FCNTX)
Manager: Will Danoff  Tenure since: 1990-09 (35 yrs)
AUM: $140B  Style: Large Growth

=== Performance Review (3-year) ===
Annualized return: 12.5% (top 25% of category)
Sharpe ratio: 0.85 (top 20% of category)
Max drawdown: -28.3% (category median -25.6%)
Information ratio: 0.62
Calmar ratio: 0.44
Hit rate: 58% (monthly, vs. benchmark)

=== Style Analysis ===
Regressed style: Large Growth (R²=0.91)
Style drift: low (1-year consistent with 3-year)
Concentration: top 10 holdings 68%
Turnover: 25% annualized (low turnover, long-term holder)

=== Assessment ===
Strengths: strong stock selection (significant Alpha), stable style
Weaknesses: very large AUM may limit flexibility, drawdown control is average
Recommendation: suitable as the large-growth sleeve of an FOF portfolio, 15-20% weight
```

## Notes

1. **Survivorship bias**: liquidated or merged funds may be excluded from fund databases, inflating historical average performance
2. **Size effect**: once AUM exceeds roughly $50B, small-cap strategies become hard to execute and Alpha may decline
3. **Quarter-end effect**: some funds engage in "window dressing" (buying top holdings into quarter-end to lift NAV); cross-check with mid-month data
4. **Flow impact**: large subscriptions/redemptions affect fund returns (dilution / forced selling); monitor share-count changes
5. **Fee drag**: over the long run, fee differences have a significant impact on cumulative return. A 1.5% vs 0.5% fee gap over 10 years → roughly 10% cumulative return difference
6. **"Enhanced index" in name only**: some "enhanced index" or "index-plus" funds deviate wildly from their benchmark (tracking error > 8%); they are effectively active management under a passive label

## China market notes

For A-share mutual funds, substitute the following market-specific parameters:
- Risk-free rate: 1-year Chinese government bond yield, about 2.0-2.5%; benchmark: equity funds → CSI 300, balanced funds → 60% CSI 300 + 40% ChinaBond Composite
- Style indices for regression: CSI 300 Value (399346), CSI 300 Growth (399370), CSI 500 Value (930782), CSI 500 Growth (930783)
- Screening norms: AUM CNY 200M-10B; management fee ≤ 1.5% and custody fee ≤ 0.25%; no redemption fee after holding > 1 year; annualized turnover 200-400% is normal and > 600% is high; top-10 concentration 40-70% is typical; size effect kicks in above CNY 20B
- ETF thresholds: daily turnover > CNY 100M for ample liquidity; AUM > CNY 1B for negligible closure risk, < CNY 200M needs closure-risk review
- Major A-share broad-market ETFs: Huatai-PineBridge CSI 300 ETF (510300, 0.20%), E Fund CSI 300 ETF (510310, 0.20%), ChinaAMC SSE 50 ETF (510050, 0.50%), Southern CSI 500 ETF (510500, 0.20%)
- Typical A-share drift: in 2020-2021 many "value" funds moved into new energy / semiconductors (growth); check stated vs regressed style
- Institutional ownership > 20% is disclosed semi-annually and is a useful quality filter

## Dependencies

```bash
pip install pandas numpy scipy
```
