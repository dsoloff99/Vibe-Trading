---
name: sentiment-analysis
description: Market sentiment analysis using contrarian indicators (CNN Fear & Greed, VIX, put/call ratio, AAII survey, NAAIM exposure, FINRA margin debt, crypto Fear & Greed, social-media sentiment, with A-share margin-financing and Northbound flow notes); use it when the user asks whether the market is fearful or greedy, how crowded positioning is, or how to size positions based on sentiment.
category: analysis
---

# Market Sentiment Analysis

## Overview

Quantify market sentiment by turning subjective "greed and fear" into measurable indicators. Covers five dimensions: fear & greed indices, options sentiment, leveraged money, fund flows/positioning, and social-media sentiment. Sentiment indicators are usually used as contrarian signals.

## Fear & Greed Indices

### CNN Fear & Greed Index (US equities)

```
Score range: 0-100

| Score | Sentiment | Historical signal |
|------|---------|---------|
| 0-25 | Extreme fear | Bottom zone (contrarian buy) |
| 25-45 | Fear | Near a bottom |
| 45-55 | Neutral | Wait |
| 55-75 | Greed | Near a top |
| 75-100 | Extreme greed | Top zone (contrarian trim) |

Seven components (equal-weighted):
- Market momentum: S&P 500 vs its 125-day moving average
- Stock price strength: NYSE 52-week highs vs lows
- Stock price breadth: McClellan Volume Summation Index
- Put/call ratio: CBOE 5-day average put/call
- Market volatility: VIX vs its 50-day moving average
- Safe-haven demand: 20-day stock vs Treasury return spread
- Junk-bond demand: high-yield vs investment-grade credit spread
```

### VIX (CBOE Volatility Index)

| VIX level | Regime | Signal |
|------|--------|---------|
| < 12 | Complacency | Cheap hedges; watch for shocks |
| 12-20 | Normal | No sentiment signal |
| 20-30 | Elevated | Fear building; start scaling in |
| 30-40 | Fear | Historically strong forward returns |
| > 40 | Panic | Capitulation zone (2008, 2020) |

Term structure: VIX above 3-month VIX futures (backwardation) = acute stress; contango = calm.

### Crypto Fear & Greed Index

```
Score range: 0-100

| Score | Sentiment | Historical signal |
|------|---------|---------|
| 0-20 | Extreme fear | Bottom zone (contrarian buy) |
| 20-40 | Fear | Near a bottom |
| 40-60 | Neutral | Wait |
| 60-80 | Greed | Near a top |
| 80-100 | Extreme greed | Top zone (contrarian sell) |

Components:
- Volatility (25%): BTC 30-day / 90-day volatility
- Market momentum (25%): BTC price vs MA(30/90)
- Social media (15%): Twitter/Reddit sentiment word frequency
- Surveys (15%): investor polls
- Bitcoin dominance (10%): BTC share of total market cap
- Google Trends (10%): "Bitcoin" search interest
```

### A-share Fear & Greed Proxies (China notes)

The A-share market has no single fear & greed index; use this combination instead:

| Indicator | Source | Extreme fear | Extreme greed |
|------|--------|---------|---------|
| Shanghai Composite turnover | Exchange | <0.5% | >2.5% |
| Limit-up / limit-down count ratio | Market data | <0.3 | >5.0 |
| New brokerage accounts (weekly) | CSDC | <200k | >1M |
| Margin balance change (monthly) | Exchange | Net outflow >CNY 50B | Net inflow >CNY 100B |
| ETF net creations | Fund data | Broad-index ETF net creations (dip buying) | Net redemptions (profit taking) |

### How to Use Fear & Greed Readings

```
Core principle: be greedy when others are fearful, fearful when others are greedy

In practice:
1. Extreme fear (<25): scale-in signal
   - Do not go all in at once; buy in 3-5 tranches
   - Confirm fundamentals are intact (fear from a crash, not from a blow-up)

2. Extreme greed (>75): scale-out signal
   - Do not short (the trend can persist)
   - Trim to a safe level (e.g. from 80% invested down to 50%)

3. Neutral zone: sentiment carries no edge; look at other factors
```

## Put/Call Ratio

### Definition and Interpretation

```
Put/Call Ratio = put option volume / call option volume

| PCR | Meaning | Signal (contrarian) |
|-----|------|----------------|
| > 1.5 | Extreme bearishness | Bullish (excess fear) |
| 1.0-1.5 | Bearish lean | Mildly bullish |
| 0.7-1.0 | Neutral | No clear signal |
| 0.5-0.7 | Bullish lean | Mildly bearish |
| < 0.5 | Extreme bullishness | Bearish (excess greed) |
```

### PCR Reference Ranges by Market

| Market | Source | Normal range | Extreme zone |
|------|--------|---------|---------|
| US (CBOE total put/call) | CBOE | 0.7-1.2 | <0.5 or >1.5 |
| US (CBOE equity-only put/call) | CBOE | 0.5-0.8 | <0.4 or >1.0 |
| A-share (SSE 50 ETF options) | SSE | 0.5-1.5 | <0.3 or >2.0 |
| BTC (Deribit) | Deribit | 0.3-0.8 | <0.2 or >1.2 |

### Combining PCR with VIX

```
High PCR + high VIX = extreme panic (strong contrarian buy / reversal signal)
Low PCR + low VIX = extreme complacency (watch for black swans)
High PCR + low VIX = hedging demand (institutions protecting longs)
Low PCR + high VIX = conflicting signal (needs more confirmation)
```

## Leverage Signals

### FINRA Margin Debt (US)

```
Margin debt = money borrowed against brokerage accounts to buy securities (bullish leverage)
Published monthly by FINRA (about 3 weeks after month-end)

Margin-debt indicators:
- Level: total leverage in the system (roughly $800-900B in 2024; peak ~$935B in Oct 2021)
- Rate of change: YoY and 3-month change matter more than the level
- Ratio: margin debt / total US market cap, typically 1.5-2.5%
- Free credit balances: cash sitting in accounts (dry powder); negative net worth (debt > cash) = stretched
```

### Margin-Debt Signals

| Indicator | Bullish signal | Bearish signal |
|------|---------|---------|
| Margin debt level | Stabilizes after a drawdown, then rises | Accelerates at highs (overheated) |
| YoY change | Turns up from below -20% (deleveraging done) | > +50% YoY (preceded 2000, 2007, 2021 tops) |
| Free credit balances | Rising while margin debt falls (cash build) | Falling toward zero while debt rises |
| Debt / market cap | Falls back after a spike | Extreme highs (leverage too high) |

### Margin-Debt Historical Thresholds (US)

```
2000 top: +80% YoY growth into the peak
2007 top: +60% YoY growth into the peak
2021 top: ~$935B, +70% YoY
2022 bottom: about -25% YoY (deleveraging complete)

Rule of thumb: YoY growth > +50% -> overheating warning
               YoY decline > -20% -> capitulation / bottoming signal
```

### A-share Margin Financing (China notes)

```
Margin buying = borrowing cash to buy stock (bullish leverage)
Securities lending = borrowing stock to sell (bearish leverage)

Margin balance: about CNY 1.5-1.8T in 2024, typically 2-3% of total A-share market cap
2015 bull-market top: CNY 2.27T (extreme); 2018 bear-market bottom: CNY 0.76T
Rule of thumb: monthly change > +10% -> overheating; > -10% -> panic
Signals: 5 consecutive days of net margin buying = bullish; sudden jump in securities-lending
         balance = someone is shorting; margin data is published T+1
```

## Fund Flow and Positioning Signals

### Investor Surveys and Manager Exposure (US)

```
AAII Investor Sentiment Survey (weekly, individual investors):
  Long-run averages: bulls ~37.5%, bears ~31%, neutral ~31.5%
  Contrarian extremes: bull-bear spread > +30 = excess optimism; < -30 = excess pessimism
  Bears > 50% has historically preceded strong 6-12 month returns (2009, 2022)

NAAIM Exposure Index (weekly, active managers' average equity exposure):
  Range: -200 (fully leveraged short) to +200 (fully leveraged long)
  > 90 = managers fully invested (little buying power left, crowded)
  < 30 = defensive (cash on the sidelines, contrarian bullish)

Other positioning data:
  - CFTC Commitments of Traders: speculator net positioning in S&P 500 / Nasdaq futures
  - ICI weekly fund flows: equity vs money-market fund flows
  - BofA Global Fund Manager Survey: cash level > 5% = "buy" signal, < 4% = "sell" signal
```

### Positioning Signals

| Indicator | Bullish signal | Bearish signal |
|------|---------|---------|
| AAII bull-bear spread | < -30 (extreme pessimism) | > +30 (extreme optimism) |
| NAAIM exposure | < 30 for 2+ weeks | > 90 (fully invested) |
| Money-market fund assets | Record highs (sidelined cash) | Sharp outflows into equities |
| Fund manager cash | > 5% | < 4% |

### Northbound Flows (China notes)

```
Northbound flows = foreign money buying A-shares through Shanghai/Shenzhen-Hong Kong Stock Connect

Key features:
1. Size: cumulative net buying of roughly CNY 2T
2. Style: favors blue chips (consumer, financial and tech leaders)
3. Leading tendency: has historically added at market bottoms
4. Limitation: since 2023, passive (ETF) flows dominate, so stock-picking signal has weakened

Signals: daily net inflow > CNY 10B (strong) / < -CNY 10B; > 10 consecutive days of inflows or outflows;
         monthly net > CNY 50B / < -CNY 50B
Caveats: hedging trades and "fake foreign" money (mainland capital routed via HK) distort daily prints;
         disclosure rules changed in 2023, so use weekly/monthly totals and cross-check with margin balances and ETF flows
```

## Social-Media Sentiment Analysis

### Sentiment Quantification Framework

```
Data sources:
- English: Twitter (X) / Reddit (r/wallstreetbets, r/stocks) / StockTwits / Telegram
- Chinese: Xueqiu / Eastmoney Guba / Weibo / WeChat public accounts
- Crypto: Crypto Twitter / Discord / Telegram groups

Quantified dimensions:
1. Discussion heat: mention frequency / baseline frequency
2. Sentiment polarity: share of positive / negative / neutral posts
3. Sentiment intensity: mean positive score - mean negative score
4. Sentiment change: direction of change versus the prior period
```

### Sentiment Indicators

| Indicator | Calculation | Contrarian signal |
|------|------|---------|
| Heat index | Search / discussion volume vs MA(30) | Spike in heat = overheated |
| Bullish share | Bullish posts / total posts | >80% = extreme optimism (warning) |
| Newcomer index | Share of posts from newly created accounts | >50% = retail rush (top) |
| Influencer consensus | Agreement among large accounts | Unanimous bullishness = danger |

### Social-Media Sentiment Cycle

```
Bottom: nobody talks -> a few contrarians buy -> controversy phase
Rally: discussion grows -> optimism spreads -> newcomers pile in
Top: everyone talks -> extreme optimism -> skeptics get mocked
Decline: controversy -> panic -> nobody talks (back to bottom)

Cocktail-party indicator: when your Uber driver or barber starts recommending stocks = top
```

## Composite Sentiment Scoring Framework

### Scoring Model

```
Composite sentiment = 0.25×Fear&Greed + 0.20×PCR/VIX + 0.20×Leverage + 0.20×Positioning + 0.15×Social

Each dimension is normalized to 0-100:
0-20: extreme fear
20-40: fear
40-60: neutral
60-80: greed
80-100: extreme greed
```

### Sentiment to Action Mapping

| Composite sentiment | Suggested exposure | Action |
|---------|---------|------|
| 0-20 | 80-100% | Contrarian full position |
| 20-40 | 60-80% | Scale in gradually |
| 40-60 | 40-60% | Standard position |
| 60-80 | 20-40% | Scale out gradually |
| 80-100 | 0-20% | Contrarian exit |

## Output Format

```markdown
## Market Sentiment Analysis

### Sentiment Dashboard
| Indicator | Current | Percentile | Signal |
|------|--------|------|------|
| CNN Fear & Greed | 72 | 75% | Greed |
| VIX | 13.5 | 20% | Complacent |
| CBOE equity put/call | 0.55 | 25% | Optimistic |
| FINRA margin debt (YoY) | +28% | 80% | Leverage accelerating |
| AAII bull-bear spread | +22 | 70% | Optimistic |
| NAAIM exposure | 92 | 85% | Fully invested |

### Composite Sentiment Score: 68/100 (greed zone)

### Interpretation
Sentiment is tilted toward greed, with several indicators pointing to optimism:
- Margin debt is growing quickly; leveraged money is aggressive
- Active managers are fully invested; little sidelined buying power remains
- The put/call ratio is low; the options market is not hedging

### Suggested Actions
- Suggested exposure: reduce to 40-50%
- Do not chase; wait for a pullback before adding
- Consider buying put protection while VIX is cheap

### Risk Notes
- Sentiment indicators are contrarian, not precise timing tools
- In a strong trend, sentiment can stay extreme for a long time
```

## Notes

1. **Contrarian is not precise timing**: sentiment can stay in extreme zones for a long time; never short or go long on sentiment alone
2. **Combine sentiment with trend**: greed in an uptrend is normal, and fear in a downtrend is normal
3. **Different markets, different thresholds**: sentiment thresholds differ widely across US, A-share and crypto markets
4. **Data access limits**: some sentiment data requires paid APIs (e.g. Bloomberg sentiment indicators, Glassnode)
5. **Social media is noisy**: bots and promotional accounts distort sentiment analysis and must be filtered
6. **Publication lags**: FINRA margin debt is monthly with a ~3-week lag; AAII/NAAIM are weekly; A-share margin data is published T+1
7. **Northbound data changes**: A-share Northbound disclosure rules changed in 2023, so real-time data is less transparent than before
