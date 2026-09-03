---
name: convertible-bond
description: Convertible bond analysis covering three-way valuation (bond floor, conversion value, option value), call/put/reset term analysis, cheapness screens and rotation frameworks, with China A-share market notes on conversion-price resets, forced redemption, put clauses and the double-low strategy; use it when the user asks to value, screen, or trade convertible bonds.
category: asset-class
---

# Convertible Bond Analysis

## Overview

A convertible bond is a hybrid instrument with a "bond floor plus equity option" profile. This skill covers three-way convertible valuation, analysis of the embedded terms (calls, puts, resets), cheapness screens and a rotation framework for selecting converts. It applies to US converts by default, with A-share specifics collected in the China market notes at the end.

## Convertible Bond Basics

### Core Elements

| Element | Description | Example (US) |
|------|------|------|
| Par value | $1,000 per bond; prices quoted as % of par (100 = par) | - |
| Coupon | Fixed, usually 0%-3% for US issuers (A-share coupons step up over time) | Uber 0.875% 2028, MicroStrategy 0% 2030 |
| Conversion price | Stock price at which the bond converts into shares | Conversion price $50.00 (ratio 20 shares per $1,000) |
| Maturity | Usually 5-7 years (A-share: 6 years) | 2024-2029 |
| Redemption at maturity | Par (A-share: par + final coupon + premium, 110-115) | 100 |
| Investor put | Holder can sell the bond back at par on set dates (common in older US deals) | Put at par on year 5 |
| Issuer call | Issuer can redeem early once the stock stays far above the conversion price | Soft call at 130% for 20 of 30 trading days after the non-call period |
| Reset (downward revision) | Conversion price can be lowered (rare in US deals; standard in A-share) | Reset if the stock stays below 85% of the conversion price |

### Key Metrics

```
Conversion value = par / conversion price × stock price
                 = 100 / 50.00 × 60.00 = 120.00

Conversion premium = (bond price - conversion value) / conversion value × 100%
                   = (125 - 120) / 120 × 100% = 4.17%

Bond floor = Σ(coupon / (1+r)^t) + redemption price / (1+r)^n
           ≈ 85-95 (depends on remaining term, credit spread and rates)

Bond-floor premium = (bond price - bond floor) / bond floor × 100%
```

## Three-Way Valuation

### 1. Bond Floor (debt value)

```python
def bond_floor(coupon_rates: list, years_remaining: float,
               redemption_price: float = 110, yield_rate: float = 0.03) -> float:
    """
    Args:
        coupon_rates: coupon rates for each remaining year, e.g. [0.8, 1.0, 1.5, 2.0]
        years_remaining: years to maturity
        redemption_price: redemption price at maturity
        yield_rate: discount rate (comparable corporate-bond yield, roughly 2.5-4% for A-share;
                    use the issuer's straight-debt yield, e.g. 5-8%, for US high-yield issuers)
    Returns:
        bond floor (debt value)
    """
    pv = sum(c * 100 / (1 + yield_rate)**i for i, c in enumerate(coupon_rates, 1))
    pv += redemption_price / (1 + yield_rate)**len(coupon_rates)
    return pv
```

**What the bond floor means**:
- Higher bond floor -> stronger downside protection -> limited room to fall
- Typically the bond floor sits between 85 and 100 (lower for 0% US converts from high-yield issuers)
- A convert trading near its bond floor is a "busted" or debt-like convert: safe but with little upside

### 2. Conversion Value (equity value)

```
Conversion value = 100 / conversion price × current stock price

Drivers:
- Stock price (positive)
- Conversion price (negative)
- Downward reset of the conversion price -> conversion value rises
```

### 3. Option Value

```
Option value = bond price - max(bond floor, conversion value)

High option value -> the market expects stock upside or (A-share) a likely conversion-price reset
Low or negative option value -> cheap (possible opportunity, or a credit problem)
```

### Three-Way Classification Matrix

| Conversion value | Bond floor | Convert type | Strategy |
|---------|---------|---------|------|
| >120 | Irrelevant | Equity-like (in the money) | Tracks the stock; watch call risk |
| 100-120 | Irrelevant | Balanced | Best zone: upside participation with downside cushion |
| <100 | >90 | Debt-like (busted) | Collect the yield; wait for a reset or a stock rebound |
| <80 | <85 | Distressed | High risk; possible credit event |

## Term Analysis

### Issuer Call

**Typical US terms**: soft call once the stock closes above 130% of the conversion price for 20 of 30 consecutive trading days after the non-call period (usually 3 years); some deals have a hard call date instead.

```
Assessing call risk:
1. Stock persistently above 130% of conversion price and non-call period expired -> high probability
2. Issuer can refinance more cheaply -> high probability (call to force conversion and remove the debt)
3. Issuer wants to avoid dilution -> lower probability (call forces conversion into shares)

What a call does:
- Holders must convert (or sell) before the redemption date or receive only par
- Caps the bond price near conversion value; the convert loses its premium
- Option value collapses toward zero
```

### Investor Put

**Typical US terms**: holder may put the bond to the issuer at par plus accrued interest on a fixed date (often year 5 of a 7-year deal); also triggered by a fundamental change (takeover).

```
Put = the investor's right to sell the bond back to the issuer at par plus accrued interest

Issuer responses:
1. Refinance and honor the put -> pay cash
2. Sweeten terms (coupon step-up or conversion-price reset) -> discourage the put
3. Buy back bonds in the open market ahead of the put date

Investor strategy:
- Hold a busted convert trading below par into the put date -> yield-to-put is the floor return
- Fundamental-change put + make-whole table -> protection in a takeover
```

### Conversion-Price Reset

**Where it applies**: standard in A-share deals (see China market notes); in US deals only as anti-dilution adjustments (stock splits, special dividends) or in death-spiral structures of small-cap issuers.

```
Effect of a reset:
- Conversion value = 100 / new conversion price × stock price, rises immediately
- Bond price usually rises 5-15%
- The stock may fall on dilution expectations
```

## Cheapness Screen

### Screen Logic

```
Cheapness score = bond price + conversion premium × 100

Lower score -> low price + low premium -> better risk/reward

Filters:
1. Score < 130 (strict) or < 150 (loose)
2. Bond price < 115 (safety)
3. Conversion premium < 30% (upside participation)
4. Remaining term > 1 year (avoid maturity pressure)
5. Credit: issuer with positive free cash flow or investment-grade rating (avoid credit risk)
6. Issue size > $300M (liquidity; US converts trade OTC)
```

### Screen Example

```markdown
### Cheapness Ranking Top 10

| Rank | Convert | Price | Premium | Score | Rating | Years left |
|------|--------|------|--------|--------|------|---------|
| 1 | XYZ 0.25% 2029 | 105.2 | 12.3% | 117.5 | BB+ | 3.2 |
| 2 | ABC 1.50% 2028 | 108.5 | 15.6% | 124.1 | BBB- | 2.8 |
| ... | ... | ... | ... | ... | ... | ... |
```

**Historical reference** (US balanced converts, ICE BofA US Convertible Index):
- Annualized return: roughly 60-70% of equity upside with 40-50% of the drawdown
- Maximum drawdown: about -25% in 2008, -15% in 2022
- Sharpe: 0.6-0.9 over full cycles
- Key risks: credit risk (small-cap 0% coupon issuers), rate sensitivity for busted converts

## Convertible Rotation Strategy

### Rotation Dimensions

| Dimension | Indicator | Signal |
|------|------|------|
| Price | Bond price | <110 very cheap, 110-120 fair, >130 expensive |
| Participation | Conversion premium | <10% high delta, 10-30% balanced, >50% pure debt |
| Safety | Bond floor / price | >0.9 = large margin of safety |
| Terms | Call / put / reset outlook | Put date near + below par = protected; call risk = cap |
| Stock | Stock momentum | Positive stock trend = source of upside |

### Rotation Process

```
1. Screen the universe (exclude: matured / called / distressed credits)
2. Score each dimension
3. Rank by composite score
4. Select the top 15-20 equal-weighted
5. Rebalance monthly
```

## Output Format

```markdown
## Convertible Bond Analysis: [Issuer coupon maturity / CUSIP]

### Basic Information
| Metric | Value |
|------|-----|
| Current price | 112.50 |
| Conversion value | 98.30 |
| Bond floor | 92.15 |
| Conversion premium | 14.4% |
| Bond-floor premium | 22.1% |
| Cheapness score | 126.9 |
| Years to maturity | 3.5 |
| Rating | BB+ |

### Three-Way Valuation
- **Downside protection**: bond floor 92.15; about 18% of downside before the floor
- **Equity participation**: premium 14.4% is low; a 10% stock rally should lift the bond about 8%
- **Option value**: price - max(bond floor, conversion value) = 14.2; reasonable

### Term Analysis
- **Call risk**: low (stock is 35% below the 130% call trigger; non-call period ends in 18 months)
- **Put protection**: put at par in 2.5 years -> yield-to-put about 1.2%
- **Reset**: none (anti-dilution adjustments only)

### Investment View
Cheapness score 126.9 sits in the attractive zone. Suggested...
```

## Notes

1. **Credit risk is the biggest landmine**: small-cap 0% coupon issuers have defaulted or restructured; be cautious with unrated or low-rated converts
2. **Watch the call clock**: after a call notice, failing to convert or sell means receiving par; check call notices daily
3. **Liquidity risk**: US converts trade OTC (144A) and small issues may not trade for days; large positions are hard to exit; retail investors often access the asset class via ETFs (CWB, ICVT)
4. **Terms differ deal by deal**: call triggers, put dates, make-whole tables and dilution adjustments vary; read the indenture for each bond
5. **Holding to maturity without converting**: you only receive par plus coupons; buying well above par and holding to maturity locks in a loss
6. **Data access**: US convert terms come from the prospectus/indenture (SEC EDGAR); prices from FINRA TRACE; stock OHLCV via the standard market-data interface
7. **Backtest limitations**: convertible backtests need conversion prices, call/put schedules and credit data beyond stock data, so they are more complex than equity backtests

## China Market Notes (A-share Convertibles)

A-share converts have standardized terms and trade T+0 on the exchanges, which creates a distinctive "term game" and a well-known cheapness strategy.

### Standard A-share Terms

| Element | Description | Example |
|------|------|------|
| Par value | CNY 100 | - |
| Coupon | Step-up, usually 0.3%-2.0% | Year 1: 0.4% ... Year 6: 2.0% |
| Maturity | Usually 6 years | 2024-2030 |
| Redemption at maturity | Par + final coupon + premium | 110-115 |
| Put clause | Puttable if the stock stays below 70% of the conversion price | 30 consecutive trading days below 70% (last 2 interest years) |
| Forced redemption | Callable if the stock stays above 130% of the conversion price | 15 of 30 consecutive trading days above 130% |
| Downward reset | Conversion price can be lowered | 15 of 30 consecutive trading days below 85% |

### Downward Reset Game

```
Reset probability assessment:
1. Trigger met or nearly met -> high probability
2. Major shareholder holds a large unconverted position -> high probability (incentive to reset)
3. Company is about to face a put -> high probability (reset to avoid the put)
4. Company is cash-rich with no repayment pressure -> low probability (no incentive)
5. Conversion would heavily dilute control -> low probability (control concerns)

After a reset: conversion value jumps, bond price typically rises 5-15%, stock may fall on dilution
```

### Forced Redemption Game

```
Handling a forced redemption:
1. Redemption announced -> must convert or sell before the redemption date
2. Redemption price is usually 100.xx -> far below conversion value
3. Not converting = large loss (e.g. bond at 160, redeemed at 100)

Redemption signals:
- Stock persistently above 130% of the conversion price -> count the days
- Company announces "no early redemption" -> temporarily safe
- Conversion progress > 90% -> redemption may not be exercised
```

### Put Game

```
Put = the investor's right to sell back to the company at par plus interest

Company responses: reset the conversion price (avoid the put) / support the stock price / accept the put and pay
Investor strategy: hold converts near the bond floor during the put window -> put is the floor;
                   reset expectations -> earn the reset gain
```

### Double-Low Strategy

```
Double-low score = bond price + conversion premium × 100
Filters: score < 130 (strict) or < 150 (loose); price < 115; premium < 30%;
         remaining term > 1 year; credit rating >= AA-
```

```python
class ConvertibleBondEngine:
    """Double-low strategy signal engine"""
    def generate(self, data_map):
        # Compute the double-low score at each month-end
        # Select the top N, equal-weighted
        # Rebalance at the start of the next month
        pass
```

**Historical reference** (A-share converts): annualized 10-15%, max drawdown -8% to -15%, Sharpe 1.0-1.5; key risk is credit (small-cap convert defaults such as Soute convertible). Exclude converts that have delisted, announced forced redemption, or are rated below A+; A-share convert data comes from the tushare convertible-bond interface, and OHLCV is available through the standard interface.
