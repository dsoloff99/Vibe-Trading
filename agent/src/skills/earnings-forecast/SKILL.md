---
name: earnings-forecast
description: Forecast company earnings and analyze consensus expectations using top-down and bottom-up methods, standardized unexpected earnings (SUE), post-earnings-announcement drift (PEAD), and analyst estimate-revision momentum; use when projecting EPS, comparing a forecast against consensus, or trading earnings surprises.
category: analysis
---
# Earnings Forecasting and Consensus Expectations

## Overview

Build trading signals around company earnings forecasts and their deviation from market consensus. Core logic: short-term stock prices are driven by the gap between results and expectations, so capturing the "expectation gap" is more valuable than forecasting absolute earnings. Two main threads: (1) compare an independent forecast with consensus to find deviations; (2) track analyst estimate-revision momentum.

## Core Concepts

### 1. Top-Down Forecasting

**Forecast chain:**

```
GDP growth forecast → industry value-added growth → industry revenue growth → leading-company revenue growth → margin assumptions → EPS forecast
```

**Worked example (US smartphone / consumer tech):**

| Level | Metric | Forecast logic |
|------|------|---------|
| Macro | GDP +2.5% | Consumer spending is ~68% of GDP, consumption growth about +3% |
| Industry | Smartphone revenue +3% | Premium-tier mix shift, ASP-led growth |
| Company | Apple (AAPL.US) | iPhone ASP +5%, units +1%, revenue about +6% |
| Profitability | Net margin 26% | Services mix lifts margin, opex ratio stable |
| EPS | about $7.50 | Net income / diluted shares (buybacks add ~3%) |

**Use cases:** judging sector beta, locating the market-wide earnings cycle, coordinating with macro strategy

### 2. Bottom-Up Forecasting

**Three ways to decompose revenue:**

```python
# Method 1: volume x price
revenue = volume * price
# e.g., Exxon Mobil (XOM.US) = barrels produced x realized oil price + downstream/chemicals revenue

# Method 2: customer / product segments
revenue = sum(segment_revenue for segment in business_lines)
# e.g., Microsoft (MSFT.US) = Productivity & Business Processes + Intelligent Cloud + More Personal Computing

# Method 3: stores / users
revenue = stores * revenue_per_store  # or users * ARPU
# e.g., Chipotle (CMG.US) = store count x traffic per store x average ticket x operating days
```

**Key points for margin assumptions:**
- Gross margin: change in raw-material cost share, product-mix upgrades
- Opex ratio: operating leverage (revenue up, opex ratio down), changes in R&D spend
- Tax rate: 21% US federal statutory (about 24-25% effective with state tax) vs lower effective rates for companies with foreign income or R&D credits; check for expiring tax incentives

### 3. Standardized Unexpected Earnings (SUE)

**Formula:**

```python
SUE = (actual_EPS - consensus_EPS) / std(actual_EPS - consensus_EPS)
# consensus_EPS = analyst consensus EPS (use the median)
# std = standard deviation of forecast errors over the past 8 quarters
```

**Signal thresholds (empirical reference):**

| SUE range | Meaning | Trading action |
|---------|------|---------|
| SUE > +2.0 | Large beat | Strong buy signal |
| SUE +1.0~+2.0 | Modest beat | Buy signal |
| SUE -1.0~+1.0 | In line | No signal |
| SUE -2.0~-1.0 | Modest miss | Sell signal |
| SUE < -2.0 | Large miss | Strong sell signal |

### 4. Post-Earnings-Announcement Drift (PEAD)

**Phenomenon:** after an earnings release, the stock keeps drifting in the direction of the surprise for 30-60 trading days.

**US PEAD strategy implementation:**

```python
# Strategy logic
# 1. Earnings announcement date (quarterly 10-Q / annual 10-K; most companies report 2-5 weeks after quarter end)
# 2. Compute SUE
# 3. Buy stocks with SUE > +1.5 and hold for 40 trading days
# 4. Sell / short stocks with SUE < -1.5 (shorting is available in the US market)

# Key parameters
holding_period = 40      # holding period in trading days
sue_threshold = 1.5      # SUE threshold
max_positions = 10       # maximum number of positions
rebalance_on = "earnings_date"  # rebalance on the earnings announcement date
```

**US PEAD caveats:**
- Shorting is possible but borrow cost and squeeze risk matter; a long-only or long-biased version is simpler for an individual investor
- Pre-announcements and guidance updates (filed on Form 8-K) arrive before the formal report and get priced first
- Earnings seasons cluster (mid-Jan to mid-Feb, mid-Apr to mid-May, mid-Jul to mid-Aug, mid-Oct to mid-Nov); spread entries across the crowded window

### 5. Analyst Estimate-Revision Momentum

**Three key metrics:**

```python
# 1. Estimate revision ratio (ERM)
ERM = (number of upgrades - number of downgrades) / total covering analysts
# ERM > 0.3 = positive momentum, ERM < -0.3 = negative momentum

# 2. Magnitude of consensus change
eps_change_pct = (new_consensus - old_consensus_30d_ago) / abs(old_consensus_30d_ago)
# change > +5% = significant upward revision

# 3. Estimate dispersion
dispersion = std(all_analyst_EPS) / mean(all_analyst_EPS)
# dispersion > 0.3 = wide disagreement, high uncertainty
# dispersion < 0.1 = strong consensus, high certainty
```

**Estimate-revision momentum strategy:**
- Buy: ERM > +0.3 and eps_change_pct > +5% and dispersion < 0.25
- Sell: ERM < -0.3 and eps_change_pct < -5%
- Signal horizon: about 60-90 trading days (revision momentum decays)

## Analysis Framework

### Four-Step Earnings Analysis

1. **Build the forecast**: choose Top-Down or Bottom-Up and output an EPS estimate
2. **Get consensus**: pull consensus EPS from FactSet / Bloomberg / LSEG I/B/E/S, or free sources such as Yahoo Finance and Zacks
3. **Compute the deviation**: SUE or a simple percentage gap, to determine beat/miss direction
4. **Generate the signal**: apply SUE thresholds to generate trades and manage position size with the PEAD holding period

### Earnings Calendar (key US dates)

| Timing | Event | Strategy action |
|------|------|---------|
| Early-mid January | Pre-announcement / guidance-update season (8-K) | Capture the expectation gap early |
| Mid-Jan to mid-Feb | Q4 and full-year earnings season | Confirm SUE, open PEAD positions |
| 60-90 days after fiscal year end | 10-K filing deadline | Late filing (NT 10-K) = negative signal |
| Mid-Apr to mid-May | Q1 earnings season | First-half estimate revisions |
| Mid-Jul to mid-Aug | Q2 earnings season | Same as above |
| Mid-Oct to mid-Nov | Q3 earnings season | Q3 data validates full-year expectations |

### Expectation-Gap Portfolio Construction

```python
# Portfolio construction parameters
config = {
    "universe": "S&P 500 constituents",   # liquidity guarantee
    "signal": "SUE > +1.5 or ERM > +0.3", # beat / revision signal
    "max_positions": 20,                  # maximum positions
    "position_weight": "equal",           # equal weight
    "holding_period": 40,                 # trading days
    "rebalance": "earnings_calendar",     # rebalance on the earnings calendar
    "stop_loss": -0.08,                   # 8% stop loss
}
```

## Output Format

```
## Earnings Forecast Analysis - [Ticker] [Company name]

### Earnings forecast
- Method: [Top-Down / Bottom-Up]
- Forecast EPS: [$X]
- Basis: [revenue growth X%, margin X%, key assumptions]

### Consensus comparison
- Consensus EPS: [$X] (source: [FactSet / Yahoo Finance], [N] analysts covering)
- Forecast deviation: [+X% / -X%]
- SUE: [+X.X]
- Estimate dispersion: [X.X] ([high / low disagreement])

### Analyst momentum
- ERM (estimate revision ratio): [+X.X] ([N] upgrades / [M] downgrades in the past 30 days)
- Consensus change: [+X%]

### Signal
- SUE signal: [strong buy / buy / none / sell / strong sell]
- Momentum signal: [positive / neutral / negative]
- PEAD entry window: [yes / no] ([X] days since the earnings release)

### Risks
- [specific risks: one-time gains, accounting-policy changes, goodwill impairment, etc.]
```

## Notes

- Consensus data requires paid terminals (Bloomberg / FactSet / LSEG); free sources (Yahoo Finance, Zacks) may lag
- SUE needs at least 8 quarters of historical forecast errors to estimate the standard deviation
- Pre-announcements and guidance updates are earlier signal sources than the formal report, but less precise
- Earnings seasons are crowded (four windows a year); PEAD signals may interfere with each other
- One-time items (asset sales / litigation settlements / investment gains) distort GAAP EPS; strip non-recurring items and use adjusted (non-GAAP) EPS
- Estimate-revision momentum is self-reinforcing (analyst herding); identifying inflection points is more valuable than trend following
- Small caps have thin analyst coverage (< 3 analysts), so consensus is statistically weak; prefer S&P 500 / Russell 1000 constituents
- This framework is for research and backtesting only and does not constitute investment advice

## China market notes

- A-share worked examples for the same methods: top-down on the baijiu industry (GDP +5%, consumption ~65% of GDP, industry revenue +8%, Kweichow Moutai 600519.SH ex-factory price +10% and volume +2%, net margin 55%, EPS about CNY 62); bottom-up volume x price for China Shenhua (601088.SH), segments for Midea (000333.SZ), stores x table turnover x ticket for Haidilao (6862.HK)
- Tax rate: 15% for high-tech enterprises vs 25% standard; check for expiring preferential treatment
- Reporting calendar: preliminary earnings warnings (yeji yugao) peak in mid-January and mid-July, formal annual reports by April 30, interim reports by August 31, Q3 reports by October 31; a missed deadline is a negative signal
- Shorting is restricted (securities lending), so A-share PEAD is usually long-only; the April and August windows are especially crowded
- Consensus sources: Wind / Choice / East Money / Tonghuashun; use EPS excluding non-recurring items (koufei EPS); universe: CSI 300 / CSI 500 constituents
