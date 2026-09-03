---
name: sector-rotation
description: Analyze sector rotation across GICS sectors with a prosperity (business-cycle) scoring model, sector momentum ranking, supply-chain transmission analysis, and a valuation/earnings/fund-flow comparison framework; use when deciding which sectors or sector ETFs to overweight or underweight.
category: asset-class
---

# Sector Rotation Analysis

## Overview

Using the GICS sector classification (the 11 S&P 500 sectors and their SPDR sector ETFs), analyze sector rotation across four dimensions - prosperity scoring, momentum ranking, valuation comparison, and fund flows - and output sector overweight/underweight recommendations.

## GICS Sector Classification

### Level-1 sectors (11)

| Group | Sectors | ETF example |
|------|------|---------|
| Upstream cyclicals | Energy, Materials | Energy ETF: XLE |
| Midstream manufacturing | Industrials (machinery, aerospace & defense, transportation), autos | Industrials ETF: XLI |
| Downstream consumer | Consumer Staples, Consumer Discretionary, Health Care | Staples ETF: XLP |
| TMT | Information Technology, Communication Services | Technology ETF: XLK |
| Financials & real estate | Financials, Real Estate | Financials ETF: XLF |
| Utilities & defensives | Utilities, dividend payers | Utilities ETF: XLU |

### Sector cycle characteristics

| Type | Sectors | Traits | Drivers |
|------|------|------|---------|
| Deep cyclicals | Energy / Materials / Industrials | Volatile earnings, tightly linked to macro | PPI, ISM PMI, commodity prices |
| Defensive | Consumer Staples / Health Care / Utilities | Stable earnings, defensive | CPI, consumer-spending data |
| Growth | Information Technology / Communication Services / clean energy | High P/E, high growth, policy sensitive | Industrial policy, adoption rates |
| Financials | Banks / capital markets / insurance | Spread-driven, positively correlated with rates | Fed funds rate, credit growth, loan demand |

## Prosperity Scoring Framework

### Scoring dimensions (100 points)

| Dimension | Weight | Metric | Scoring rule |
|------|------|------|---------|
| Earnings growth | 30% | Net income YoY growth | >30%=30 pts, 15-30%=22, 0-15%=15, <0%=5 |
| Earnings trend | 20% | Consecutive quarters of acceleration | 3+ quarters=20, 2 quarters=14, decelerating=-5 |
| Activity indicators | 20% | PMI / capacity utilization / prices | High and rising=20, high but rolling over=12, low=5 |
| Policy support | 15% | Strength of industrial/fiscal policy | Clear tailwind=15, neutral=8, headwind=2 |
| Valuation safety | 15% | P/E historical percentile | <30th pct=15, 30-50th=10, >70th=3 |

### Prosperity change signals

```
Upturn signals (overweight):
1. Sector PMI > 50 for 2 consecutive months and improving MoM
2. Leading companies' orders/revenue accelerating YoY
3. Product prices rising (pricing-power cycle)
4. Capacity utilization > 80% and rising
5. Policy catalysts (subsidies / tax credits such as IRA or CHIPS / deregulation)

Downturn signals (underweight):
1. Sector PMI < 50 for 2 consecutive months
2. Days inventory outstanding rising (inventory build-up)
3. Product prices falling
4. Overcapacity (utilization < 60%)
5. Policy tightening (regulation / antitrust / drug-pricing reform)
```

## Sector Momentum Ranking

### Price momentum

```python
def sector_momentum(sector_returns: pd.DataFrame, lookback: int = 60, skip: int = 5) -> pd.Series:
    """
    Args:
        sector_returns: daily sector returns, columns = sector names
        lookback: lookback window (trading days)
        skip: skip the most recent N days (avoid short-term reversal)
    Returns:
        sector momentum score ranking
    """
    cum_return = (1 + sector_returns).rolling(lookback).apply(lambda x: x[:-skip].prod() - 1)
    return cum_return.iloc[-1].rank(ascending=False)
```

### Earnings momentum

```
Earnings momentum = current-quarter ROE YoY change - prior-quarter ROE YoY change
Positive = earnings accelerating (overweight signal)
Negative = earnings decelerating (underweight signal)
```

### Composite momentum ranking

```
Composite score = 0.4 × price momentum rank + 0.3 × earnings momentum rank + 0.3 × fund-flow rank
Overweight the top 5 sectors, underweight the bottom 5
```

## Supply-Chain Transmission

### Typical transmission chains

```
Upstream (raw materials) → Midstream (manufacturing) → Downstream (consumption / applications)

Example 1: EV battery chain
  Lithium carbonate (upstream) → cathode materials (mid) → battery cells (mid) → EV makers (downstream)
  Transmission: lithium price↑ → cathode cost↑ → cell price↑ → automaker gross margin↓

Example 2: Semiconductor chain
  Equipment / materials (upstream) → wafer fabrication (mid) → packaging & test (mid) → consumer electronics (downstream)
  Transmission: smartphone demand↑ → packaging orders↑ → fab capacity tight → equipment capex↑

Example 3: Housing chain
  Land / financing (upstream) → homebuilding (mid) → home sales / property services (downstream)
  Transmission: rate cuts → existing-home sales recover (downstream first) → housing starts↑ (mid) → land acquisition↑ (upstream)
```

### Transmission rules

| Rule | Description | Investment implication |
|------|------|---------|
| Demand flows bottom-up | Downstream demand → midstream orders → upstream raw materials | Demand inflections show up downstream first |
| Cost flows top-down | Upstream price hikes → midstream costs → downstream price increases | Upstream price hikes help upstream, hurt midstream |
| Inventory-cycle transmission | Active restocking → passive restocking → active destocking → passive destocking | Passive destocking is the buy point |
| Lead/lag | Upstream leads midstream by 1-2 quarters, midstream leads downstream by 1-2 quarters | Position ahead in the next link of the chain |

## Sector Comparison Framework

### Valuation comparison

| Metric | Use | Caveats |
|------|------|---------|
| P/E (TTM) | Earnings valuation | Cyclical P/E is distorted (a low P/E may mark the peak) |
| P/B | Asset valuation | Better for banks / real estate / cyclicals |
| P/E historical percentile | Valuation position | Use the 5-year percentile |
| PEG | Growth valuation | <1 undervalued, >2 overvalued |
| Dividend yield | Income yield | High dividend = defensive allocation |

### Earnings comparison

| Metric | Meaning |
|------|------|
| ROE | Profitability |
| Change in ROE | Earnings trend |
| Gross margin | Competitive structure |
| Net income growth | Growth |
| Cash flow / net income | Earnings quality |

### Fund-flow comparison

| Metric | Data source | Signal |
|------|--------|------|
| Institutional 13F position changes | SEC EDGAR | Institutional preference, quarterly lag |
| Margin debt change | FINRA | Direction of leveraged money |
| ETF net creations/redemptions | Fund data | Institutional and retail allocation direction |
| Block trades / dark-pool volume | Exchange / FINRA TRF | Institutional repositioning signal |

## Output Format

```markdown
## Sector Rotation Analysis

### Prosperity ranking Top 10
| Rank | Sector | Prosperity | Change | Core thesis |
|------|------|--------|------|---------|
| 1 | Information Technology | 85 | ↑+8 | AI compute demand surge |
| 2 | Industrials | 80 | ↑+5 | Reshoring + infrastructure capex |
| ... | ... | ... | ... | ... |

### Sector allocation recommendation
| Stance | Sectors | Suggested weight | Core thesis |
|------|------|---------|---------|
| Overweight | Information Technology, Industrials, Communication Services | 10-15% each | Rising prosperity + policy catalysts |
| Neutral | Consumer Staples, Health Care | 5-8% each | Defensive, reasonable valuation |
| Underweight | Real Estate, Materials | 0-3% each | Falling prosperity, policy effect uncertain |

### Supply-chain opportunities
- **AI chain**: compute (upstream) → models (mid) → applications (downstream); upstream is the highest-conviction link today
- **EVs**: lithium carbonate price bottoming, battery-cell margin recovery expected

### Risks
- ...
```

## Notes

1. **Cyclical valuation trap**: a low P/E may mark peak earnings (e.g., Energy traded near 5x in 2022 at the top of the cycle); P/B is safer
2. **Policy carries heavy weight**: sector rotation is strongly driven by Fed policy, fiscal programs (IRA / CHIPS), and regulation; policy inflections matter more than fundamental inflections
3. **Theme distortion**: short-term theme chasing (e.g., AI concept names) distorts sector momentum signals; distinguish themes from genuine prosperity
4. **Data lag**: financial statements lag by 1-2 months; high-frequency data (PMI / utilization / prices) is more timely
5. **Prefer sector ETFs**: implement sector allocation with sector ETF tickers (XLK, XLE, etc.) rather than single stocks to reduce idiosyncratic risk
6. **Rotation frequency**: do not rotate too often; monthly or quarterly rebalancing is appropriate

## China market notes

For A-shares, use the Shenwan (SW) industry classification (31 level-1 industries) in place of GICS. Representative groupings and ETF codes: upstream cyclicals (coal, non-ferrous metals, oil & petrochemicals, steel, basic chemicals; coal ETF 515220), midstream manufacturing (power equipment, machinery, defense, autos; new-energy ETF 516160), downstream consumer (food & beverage, home appliances, pharma & biotech, beauty care; consumer ETF 510150), TMT (electronics, computers, telecom, media; tech ETF 515000), financials & real estate (banks, non-bank financials, real estate; financials ETF 510230), utilities (utilities, transportation, environmental; dividend ETF 510880). A-share fund-flow proxies: northbound net inflow via Stock Connect (foreign preference, leads by 1-3 months), margin-financing balance, ETF net subscriptions, and block trades. Policy variables are especially dominant in A-shares (centralized drug procurement, carbon neutrality, semiconductor localization); the 2021 coal sector (P/E ~5x at the top) is the classic cyclical valuation trap.
