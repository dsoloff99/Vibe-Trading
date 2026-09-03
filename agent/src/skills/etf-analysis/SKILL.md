---
name: etf-analysis
description: "ETF analysis: product screening, expense-ratio comparison, tracking error, liquidity assessment, strategy applications (core-satellite, sector rotation, smart beta, arbitrage) and a data-driven framework for building ETF portfolios; use when a user wants to compare, select, monitor, or build strategies around ETFs such as SPY, QQQ, or VTI."
category: asset-class
---

# ETF Analysis Skill

## Purpose

ETFs (exchange-traded funds) are the core tool for passive investing and asset allocation. This skill covers ETF product analysis, selection methodology, strategy applications, US market specifics, and data-driven quantitative methods, providing a complete framework for building ETF-based quantitative strategies and portfolios.

---

## 1. ETF Product Classification

### 1.1 By Underlying Asset

| Type | Representative Products | Characteristics |
|------|---------|------|
| **Broad-market ETFs** | SPY / IVV / VOO (S&P 500), VTI (total US market), QQQ (Nasdaq-100), IWM (Russell 2000) | Best liquidity, lowest trading cost, suited to core positions |
| **Sector ETFs** | XLY (consumer discretionary), XLV (health care), SMH / SOXX (semiconductors), XLF (financials) | Sector-rotation tools, concentrated holdings |
| **Thematic ETFs** | ICLN (clean energy), ARKK (disruptive innovation), BOTZ (robotics / AI) | Strong narrative and hype component, short life cycles |
| **Strategy / Smart Beta ETFs** | SCHD / VYM (dividend), USMV / SPLV (low volatility), QUAL (quality), MTUM (momentum) | Explicit factor exposure; fees usually slightly above broad-market ETFs |
| **Commodity ETFs** | GLD / IAU (gold), USO (crude oil), DBA (agriculture) | Physical or futures-backed; watch roll costs on futures-based products |
| **Bond ETFs** | TLT / IEF / SHY (Treasuries), LQD (IG corporate), HYG (high yield), CWB (convertibles) | Rate sensitive; duration management is key |
| **International ETFs** | EFA (developed ex-US), EEM / VWO (emerging), EWJ (Japan), MCHI / FXI (China) | FX risk plus stale-NAV / time-zone premium effects |
| **Cash-equivalent ETFs** | BIL / SGOV (T-bills), SHV | Liquidity-management tools, not investment tools |

### 1.2 Structure Types

- **Standard ETFs**: exchange-traded, in-kind creation/redemption through authorized participants (APs); premium/discount converges automatically through arbitrage
- **ETNs (exchange-traded notes)**: unsecured bank notes that track an index; no tracking error but issuer credit risk and possible early termination
- **Index mutual funds**: the off-exchange substitute for an ETF; bought at end-of-day NAV, no premium/discount, suited to automatic periodic investing (e.g. inside a 401(k))
- **Leveraged / inverse ETFs**: constant daily leverage, with a decay effect over long holding periods (see Section 4.4)

---

## 2. Core ETF Metrics

### 2.1 Tracking Error

The single most important measure of how well an ETF replicates its index.

```
Daily tracking error = std(ETF daily return - index daily return)
Annualized tracking error = daily tracking error x sqrt(252)
```

**Rating scale (broad-market ETFs)**:
- Excellent: annualized tracking error < 0.2% (large-cap US broad ETFs such as SPY / VOO typically run well under 0.1%)
- Acceptable: 0.2% ~ 0.5%
- Poor: > 0.5%

**Sources of tracking error**:
1. Management and administrative fees (continuous drag, accrued daily)
2. Dividend handling timing (delay in reinvesting distributions)
3. Trading impact when index constituents are added or removed
4. Cash drag (temporary cash from creations/redemptions)
5. Handling of halted or hard-to-trade holdings (substitutes or cash in lieu)
6. Replication method (full replication vs sampling); securities-lending income partly offsets fees

### 2.2 Information Ratio

```
IR = (ETF annualized return - index annualized return) / annualized tracking error
```

For an ETF the IR is usually negative (fee drag); the closer to 0 the better.

### 2.3 Premium / Discount

```
Premium/discount = (ETF market price - ETF iNAV) / ETF iNAV x 100%
```

- **Premium**: price > NAV; APs sell the ETF and create new shares with the basket, and the premium converges
- **Discount**: price < NAV; APs buy the ETF and redeem it for the basket, and the discount converges
- **Abnormal premium scenarios**: international ETFs whose underlying market is closed (stale NAV), ETFs holding illiquid assets (high yield, bank loans, frontier markets), and ETFs whose creations have been suspended (e.g. USO in 2020, some single-country EM ETFs)

### 2.4 Liquidity Metrics

| Metric | Meaning | Reference Threshold |
|------|------|--------|
| Average daily dollar volume | Ease of trading | Broad-market > $50M, sector > $5M |
| Bid-ask spread | Immediate trading cost | < 0.05% is high quality |
| Order-book depth | Impact of a single large order | Top 5 levels on each side > $5M cumulative is good |
| Turnover | Activity level | Too low implies elevated liquidity risk |

Remember that the true liquidity of an ETF is the liquidity of its underlying basket (APs can create shares), so on-screen volume understates capacity for broad-market products.

### 2.5 Fee Structure

```
Total expense ratio = management fee + administrative/custody fees + index licensing fee
(excludes brokerage commissions, bid-ask spread, and creation/redemption fees)
```

**Long-term fee impact formula**:
```
N-year compounded fee drag = (1 - annual fee)^N
Example: 0.5% vs 0.15% annual fee, gap after 10 years ~ 3.5%, after 20 years ~ 6.8%
```

Expense ratios of major broad-market ETFs (2025):
- VOO / IVV / VTI: 0.03%; SPLG: 0.02%; SPY: 0.0945%; QQQ: 0.20% (QQQM: 0.15%)
- Some small or niche products: 0.5%+, a clear disadvantage for long-term holders

### 2.6 AUM and Liquidity Assessment

- **AUM thresholds**:
  - < $50M: elevated closure risk, poor liquidity
  - $50M ~ $500M: tradable, but large orders are constrained
  - > $500M: ample liquidity, active market makers
  - > $10B: flagship ETF, institutional first choice

- **Closure risk signals**: steadily shrinking AUM, average AUM below ~$50M for 90 consecutive days, issuer consolidating its product line

---

## 3. ETF Selection Methodology

### 3.1 Comparison Framework for Same-Index ETFs

The same index is often tracked by several ETFs (e.g. SPY / IVV / VOO / SPLG on the S&P 500). Selection steps:

```
Step 1: AUM screen -> drop small products under $500M
Step 2: Fee comparison -> lowest expense ratio, all else equal
Step 3: Tracking error -> compare on both 1-year and 3-year windows
Step 4: Liquidity -> average daily dollar volume, bid-ask spread
Step 5: Issuer -> indexing capability, track record
```

**Quantitative scoring model**:

```python
def etf_score(etf_data: dict) -> float:
    """
    Composite ETF score (higher is better, max 100).

    Args:
        etf_data: dict containing scale, fee, tracking_error, avg_volume, spread

    Returns:
        Composite score 0~100
    """
    score = 0.0
    # AUM score (30 points)
    scale = etf_data['scale_billion']
    score += min(30, scale / 10 * 30)

    # Fee score (25 points): lower fee, higher score
    fee = etf_data['total_fee_pct']  # annual expense ratio in percent
    score += max(0, 25 - fee * 50)

    # Tracking-error score (30 points): smaller error, higher score
    te = etf_data['tracking_error_annual_pct']
    score += max(0, 30 - te * 60)

    # Liquidity score (15 points)
    vol = etf_data['avg_daily_volume_million']
    score += min(15, vol / 10 * 15)

    return round(score, 2)
```

### 3.2 Quantifying the Long-Term Impact of Fees

```python
import numpy as np

def fee_drag_analysis(annual_return: float, years: int, fee_rates: list[float]) -> dict:
    """
    Analyze how different expense ratios drag on long-term returns.

    Args:
        annual_return: index annualized return (decimal, e.g. 0.08)
        years: investment horizon in years
        fee_rates: list of expense ratios to compare (decimal, e.g. [0.002, 0.005, 0.015])

    Returns:
        dict of terminal-value multiples and relative drag for each fee rate
    """
    results = {}
    base_value = (1 + annual_return) ** years
    for fee in fee_rates:
        net_return = annual_return - fee
        end_value = (1 + net_return) ** years
        drag = (base_value - end_value) / base_value * 100
        results[f'{fee*100:.2f}%'] = {
            'end_value_multiple': round(end_value, 4),
            'drag_pct': round(drag, 2)
        }
    return results

# Example: 8% index return, 20-year horizon
# fee_drag_analysis(0.08, 20, [0.002, 0.005, 0.015])
```

### 3.3 Market-Maker Quality Assessment

A high-quality market maker shows:
- **Stable spreads**: spread widens only modestly in volatile periods (< 3x normal)
- **Sufficient depth**: dollar size is distributed evenly across price levels
- **Quote continuity**: no frequent cancel-and-replace behavior
- **Large-order handling**: spread recovers quickly after a block trade

Assessment method:
```python
# Effective spread from Level 2 data
effective_spread = (ask_price - bid_price) / mid_price * 100  # in %

# Impact cost
# Deviation of the average fill price for buying $N from the mid price
impact_cost = (avg_buy_price - mid_price) / mid_price * 100
```

### 3.4 Issuer Strength Assessment

| Dimension | Assessment Points |
|------|---------|
| ETF assets under management | Market-wide ranking, indexing expertise |
| Tracking-error history | Stability over long windows (3+ years) |
| Product-line completeness | Breadth across broad-market, sector, and international coverage |
| Creation/redemption efficiency | Handling of in-kind baskets, custom baskets |
| Market-maker relationships | Stable relationships with leading APs and market makers |

Largest US ETF issuers by AUM: Vanguard, BlackRock (iShares), State Street (SPDR), Invesco, Charles Schwab, JPMorgan

---

## 4. ETF Strategy Applications

### 4.1 Core-Satellite Strategy

```
Total portfolio = core (70~80%) + satellite (20~30%)

Core: broad-market ETFs (VTI / VOO / SPY, plus VXUS for ex-US exposure)
  -> capture market beta, low fees, long holding period, minimal trading friction

Satellite: sector ETFs / thematic ETFs / smart beta ETFs
  -> enhance returns, deliberate exposure to specific factors, higher turnover allowed
```

**Rebalancing triggers**:
- Time-based: quarterly or semi-annually
- Drift-based: any single asset deviates from target weight by > 5%

### 4.2 Sector-Rotation ETF Strategies

**Momentum rotation**:
```python
def sector_momentum_rotation(etf_returns: pd.DataFrame, lookback: int = 20, top_n: int = 3) -> list[str]:
    """
    Momentum-based sector ETF rotation.

    Args:
        etf_returns: DataFrame of daily returns for each sector ETF, columns are ETF tickers
        lookback: lookback window (trading days)
        top_n: number of ETFs to hold

    Returns:
        List of ETF tickers to hold this period
    """
    momentum = etf_returns.tail(lookback).sum()
    selected = momentum.nlargest(top_n).index.tolist()
    return selected
```

**Macro-cycle rotation**:
| Economic Phase | Recommended Sector ETFs |
|---------|------------|
| Recovery (low -> high growth, low inflation) | Consumer discretionary (XLY), technology (XLK), small caps (IWM) |
| Overheating (high growth, high inflation) | Energy (XLE), materials (XLB), industrials (XLI) |
| Stagflation (low growth, high inflation) | Energy (XLE), utilities (XLU), consumer staples (XLP) |
| Recession (high -> low growth) | Health care (XLV), utilities (XLU), bond ETFs (TLT / AGG) |

### 4.3 Smart Beta ETF Factor Exposure Analysis

Major factors and corresponding ETFs:

| Factor | Representative ETFs | Historical Effectiveness (US) |
|------|--------|--------------|
| Value (low valuation) | VTV / IWD / VLUE | Long-run premium, but long stretches of underperformance (2010s) |
| Dividend (high yield) | SCHD / VYM / DVY | Moderate; defensive in bear markets |
| Low volatility | USMV / SPLV | Strong; better Sharpe ratio than the broad market |
| Quality (high ROE) | QUAL | Strong; compounds well over the long term |
| Momentum | MTUM | Effective short-to-medium term, crash risk at reversals |
| Small cap | IWM / VB / AVUV | Positive premium historically, higher liquidity risk |

**Factor exposure analysis code**:
```python
import pandas as pd
import numpy as np
from scipy import stats

def factor_exposure_analysis(etf_returns: pd.Series, factor_returns: dict[str, pd.Series]) -> pd.DataFrame:
    """
    Analyze an ETF's exposure to each factor (single-factor regressions).

    Args:
        etf_returns: ETF daily return series
        factor_returns: dict of factor return series {factor name: return series}

    Returns:
        DataFrame with beta, t_stat, r_squared
    """
    results = []
    for factor_name, factor_ret in factor_returns.items():
        aligned = pd.concat([etf_returns, factor_ret], axis=1).dropna()
        x = aligned.iloc[:, 1].values
        y = aligned.iloc[:, 0].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        results.append({
            'factor': factor_name,
            'beta': round(slope, 4),
            't_stat': round(slope / std_err, 2),
            'r_squared': round(r_value ** 2, 4),
            'p_value': round(p_value, 4)
        })
    return pd.DataFrame(results).set_index('factor')
```

### 4.4 Decay in Leveraged / Inverse ETFs

**Volatility decay mechanism**:

```
Constant daily leverage of N x -> compounding means long-run return != N x index return

Decay (approximate) = N^2(N-1)/2 x sigma^2 x T
where sigma is the index daily volatility and T is the holding period in days
```

**Numerical example**:
- Index annualized volatility 20%, daily volatility ~ 1.26%
- 2x leveraged ETF held for 1 year: decay ~ 2^2 x (2-1)/2 x (0.2)^2 x 1 ~ 4%

**Appropriate uses**:
- Leveraged ETFs (TQQQ, UPRO): short-term tools in strongly trending markets (hold < 1 month)
- Inverse ETFs (SQQQ, SH): market hedges, short-term bearish bets (not for long-term holding)
- **Never**: use leveraged / inverse ETFs as long-term allocation positions

### 4.5 ETF Arbitrage Strategies

**Premium/discount arbitrage** (requires AP status; creation units are typically 25,000-50,000 shares):

```
Premium arbitrage:
  ETF price > iNAV + transaction costs
  -> buy the constituent basket -> create ETF shares -> sell the ETF
  -> arbitrage profit ~ premium - impact cost - commissions

Discount arbitrage:
  ETF price < iNAV - transaction costs
  -> buy ETF shares -> redeem for the constituent basket -> sell the constituents
  -> arbitrage profit ~ discount - impact cost - commissions
```

**Cross-market arbitrage (ETF vs futures)**:
```
ES (S&P 500 e-mini futures) basis = futures price - S&P 500 index
When basis > fair basis (index x (risk-free rate - dividend yield) x time to expiry):
  -> sell futures + buy ETF (cash-and-carry)
When basis < fair basis:
  -> buy futures + sell ETF (reverse cash-and-carry, requires stock borrow)
```

**Statistical arbitrage (pairs trading)**:
```python
# Mean reversion of the spread between same-index ETFs (e.g. SPY vs IVV vs VOO)
# Spread = price difference or price ratio
# Open when the spread deviates 2 standard deviations from its history, close on reversion
spread = etf_a_price / etf_b_price
z_score = (spread - spread.rolling(60).mean()) / spread.rolling(60).std()
signal = pd.Series(0, index=z_score.index)
signal[z_score > 2] = -1   # ETF_A relatively rich: sell A, buy B
signal[z_score < -2] = 1   # ETF_A relatively cheap: buy A, sell B
```

---

## 5. US ETF Market Specifics

### 5.1 ETFs vs Index Mutual Funds

| Dimension | ETF | Index Mutual Fund |
|------|---------|-----------|
| Purchase channel | Brokerage account, intraday trading | Fund company or brokerage, end-of-day NAV |
| Creation/redemption | In-kind (APs) or secondary market (individuals) | Cash purchases and redemptions |
| Premium/discount | Exists (with an arbitrage mechanism) | None |
| Minimum trade size | 1 share (fractional shares at many brokers) | Often $1 ~ $3,000 minimum |
| Costs | Low (expense ratio + spread; usually commission-free) | Low to moderate (expense ratio; possible transaction fees) |
| Tax efficiency | High (in-kind redemptions avoid capital-gains distributions) | Lower (redemptions can force taxable distributions) |
| Best suited to | Tactical trades, large allocations, taxable accounts | Automatic periodic investing, 401(k) / IRA plans |

### 5.2 Special Considerations for International ETFs

**Sources of premium/discount**:
- Time-zone mismatch: the underlying market is closed during US hours, so the published NAV is stale and the ETF price is the market's live price discovery
- FX effects: a weaker dollar raises the NAV of unhedged foreign holdings and can attract momentum buying
- Access limits: single-country ETFs in restricted markets (e.g. India, China A-shares) can hit foreign-ownership quotas and suspend creations, breaking the arbitrage mechanism

**Premium warning thresholds**:
- < 2%: normal range, safe to allocate
- 2%~5%: clear premium, enter cautiously and wait for it to narrow
- > 5%: high premium, significant entry risk (NAV falling while the premium collapses is a double hit)

**Currency hedging**:
- Many international ETFs offer hedged versions (e.g. HEFA vs EFA, DXJ vs EWJ)
- Hedging cost ~ interest-rate differential between the US and the target market; with US rates above most developed markets in 2025, hedging foreign developed exposure has been a small positive carry, while hedging EM exposure is expensive

### 5.3 Lessons from ETNs and Closed-End Funds

**ETNs (exchange-traded notes)**:
- Unsecured debt of the issuing bank; investors carry issuer credit risk (Lehman Brothers ETNs became worthless in 2008)
- Issuers can halt creations, causing large premiums (TVIX in 2012), or terminate the note early

**Inverse-volatility and leveraged products (historical lessons)**:
- XIV (inverse VIX ETN) lost more than 90% in one session in February 2018 and was terminated
- Key lesson: constant-leverage products on volatile underlyings can be wiped out by a single tail event; termination clauses crystallize the loss
- Closed-end funds trade at persistent discounts because they lack a creation/redemption mechanism; do not confuse them with ETFs

### 5.4 Major US Index Families

**Broad-market indices**:

| Index | Constituents | Characteristics |
|------|-------|------|
| S&P 500 | 500 largest US large caps (committee-selected) | Large-cap benchmark, deepest derivatives market (ES futures / SPX options) |
| S&P MidCap 400 | 400 mid caps | Mid-cap growth, complements the 500 |
| S&P SmallCap 600 | 600 small caps with a profitability screen | Small-cap factor, higher quality than Russell 2000 |
| Russell 1000 / 2000 | Largest 1,000 / next 2,000 US stocks | Rules-based; Russell 2000 is the standard small-cap benchmark |
| Nasdaq-100 | 100 largest non-financial Nasdaq stocks | Technology and growth heavy, high volatility |
| Dow Jones Industrial Average | 30 blue chips, price-weighted | Legacy benchmark, narrow |
| CRSP US Total Market / Russell 3000 | Entire investable US market | Broadest benchmarks (VTI / IWV) |
| MSCI USA / MSCI ACWI | US large-mid caps / global all-cap | Global allocation building blocks |

**Index rebalancing patterns**:
- S&P indices: quarterly rebalance on the third Friday of March / June / September / December; ad hoc additions on corporate events
- Russell: annual reconstitution on the fourth Friday of June (the largest single-day trading event in US equities)
- Nasdaq-100: annual reconstitution in December, plus special rebalances when concentration limits are breached
- Around each event: added stocks rise and deleted stocks fall in the short term, providing event-driven opportunities

---

## 6. ETF Portfolio Construction

### 6.1 Implementing Asset Allocation with ETFs

**Classic allocation frameworks (implementable with ETFs)**:

```
60/40 stocks-bonds, US version:
  SPY 30% + IWM 20% + AGG 40% + GLD 10%
  (or VTI 40% + VXUS 20% + BND 40%)

All Weather portfolio (US version):
  Equity ETF (SPY / VTI)     30%
  Long-term Treasury ETF (TLT) 40%
  Intermediate Treasury ETF (IEF) 15%
  Gold ETF (GLD)              7.5%
  Commodity ETF (DBC / PDBC)  7.5%

Barbell strategy:
  Broad-market ETF (low-risk core)          50%
  Sector / thematic ETFs (high-beta offense) 50%
```

### 6.2 ETF Tools for Global Allocation

```
US equities:      SPY / VOO / VTI / QQQ / IWM
Developed ex-US:  VEA / EFA / IEFA
Europe:           VGK / EZU / EWG (Germany)
Japan:            EWJ / DXJ (hedged)
Emerging markets: VWO / EEM / IEMG
China:            MCHI / FXI / KWEB;  India: INDA;  Vietnam: VNM

Fixed income:
  US Treasuries:   SHY / IEF / TLT / GOVT
  Aggregate bonds: AGG / BND
  Corporate:       LQD (IG) / HYG (HY);  TIPS: TIP;  International: BNDX

Commodities:
  Gold: GLD / IAU
  Crude oil: USO / BNO
  Broad commodity index: DBC / PDBC / GSG
```

### 6.3 Rebalancing Frequency vs Trading Cost

**Rebalancing cost**:
```
Cost per rebalance ~ traded amount x (commission rate + spread/2 + impact cost)
~ traded amount x 0.01%~0.05% (broad-market ETFs, commission-free at most US brokers)

Annual rebalancing cost = cost per rebalance x average number of rebalances per year
```

**Recommended rebalancing frequency**:
- Pure passive allocation (low volatility): twice a year (June / December)
- Sector rotation (high volatility): monthly or quarterly
- Threshold method: trigger when drift from target weight > 5%; usually beats fixed frequency

**Low-cost rebalancing techniques**:
- Direct new contributions to underweight positions to reduce selling
- Route dividends to underweight assets first
- In taxable accounts, sell the highest-cost-basis lots first (specific-lot identification)

### 6.4 Tax Efficiency Considerations

US ETF tax rules (individual investors, taxable accounts):
- **Capital gains**:
  - Short-term (held 1 year or less): taxed as ordinary income
  - Long-term (held more than 1 year): 0% / 15% / 20% brackets, plus 3.8% NIIT for high earners
  - Equity ETFs rarely distribute capital gains because in-kind redemptions flush out low-basis lots
- **Distributions**:
  - Qualified dividends are taxed at long-term capital-gains rates (60-day holding rule); non-qualified dividends at ordinary rates
  - Bond ETF interest is ordinary income; Treasury interest is exempt from state tax; muni ETFs (MUB) are federally tax-exempt
  - Futures-based commodity ETFs may issue a K-1 with 60/40 treatment; physically backed gold ETFs (GLD) are taxed as collectibles (28% maximum long-term rate)
- **Tax-advantaged accounts (IRA / 401(k))**: no capital-gains tax on trades inside the account

**Tax-efficiency strategies**:
- Run high-turnover sector-rotation strategies inside an IRA where gains are not taxed
- Hold long-term positions in taxable accounts for more than 1 year before selling
- Tax-loss harvest by swapping into a similar but not "substantially identical" ETF (e.g. VOO to IVV to SPLG) while observing the 30-day wash-sale rule

---

## 7. Data Analysis Methods

### 7.1 Fetching ETF Data

For US-listed ETFs, use `get_market_data` (or the `yfinance` skill) for prices and the `us-etf-flow` skill for fund flows:

```python
import yfinance as yf
import pandas as pd

def get_us_etf_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Daily OHLCV for a US-listed ETF (e.g. 'SPY'); prices are dividend-adjusted.

    Args:
        ticker: ETF ticker, e.g. 'SPY'
        start: start date 'YYYY-MM-DD'
        end: end date 'YYYY-MM-DD'

    Returns:
        DataFrame with Open, High, Low, Close, Volume indexed by date
    """
    return yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
```

The helpers below are the reference implementation on Tushare (A-share ETFs). Swap the loader and keep the downstream math unchanged:

```python
import tushare as ts
import pandas as pd

def get_etf_list(pro: ts.pro_api) -> pd.DataFrame:
    """
    Fetch the full list of listed ETFs.

    Args:
        pro: tushare pro_api instance

    Returns:
        DataFrame of basic ETF information
    """
    df = pro.fund_basic(market='E', status='L')  # E=ETF, L=listed
    return df[['ts_code', 'name', 'management', 'found_date', 'issue_date']]


def get_etf_nav(pro: ts.pro_api, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch ETF NAV data (IOPV).

    Args:
        pro: tushare pro_api instance
        ts_code: ETF code, e.g. '510300.SH'
        start_date: start date 'YYYYMMDD'
        end_date: end date 'YYYYMMDD'

    Returns:
        DataFrame with trade_date, nav, accum_nav
    """
    df = pro.fund_nav(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df.sort_values('end_date').reset_index(drop=True)


def get_etf_daily(pro: ts.pro_api, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch ETF exchange daily quotes (market price).

    Args:
        pro: tushare pro_api instance
        ts_code: ETF code
        start_date: start date
        end_date: end date

    Returns:
        DataFrame with trade_date, open, high, low, close, vol, amount
    """
    df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df.sort_values('trade_date').reset_index(drop=True)


def get_index_daily(pro: ts.pro_api, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch benchmark index daily quotes (used for tracking-error calculation).

    Args:
        pro: tushare pro_api instance
        index_code: index code, e.g. '000300.SH' (CSI 300)
        start_date: start date
        end_date: end date

    Returns:
        DataFrame with trade_date, close
    """
    df = pro.index_daily(ts_code=index_code, start_date=start_date, end_date=end_date)
    return df[['trade_date', 'close', 'pct_chg']].sort_values('trade_date').reset_index(drop=True)
```

### 7.2 Tracking-Error Calculation Template

```python
import numpy as np
import pandas as pd


def calc_tracking_error(
    etf_prices: pd.Series,
    index_prices: pd.Series,
    annualize: bool = True
) -> dict:
    """
    Calculate an ETF's tracking error against its benchmark index.

    Args:
        etf_prices: ETF NAV series (indexed by date)
        index_prices: index price series (indexed by date)
        annualize: whether to annualize, default True

    Returns:
        dict with tracking_error, avg_daily_diff, max_daily_diff
    """
    # Align the data
    aligned = pd.concat([etf_prices, index_prices], axis=1).dropna()
    aligned.columns = ['etf', 'index']

    # Daily return differences
    etf_ret = aligned['etf'].pct_change().dropna()
    idx_ret = aligned['index'].pct_change().dropna()
    daily_diff = etf_ret - idx_ret

    # Tracking error = standard deviation of the differences
    te_daily = daily_diff.std()
    te = te_daily * np.sqrt(252) if annualize else te_daily

    return {
        'tracking_error': round(te * 100, 4),       # percent
        'avg_daily_diff': round(daily_diff.mean() * 100, 4),  # average daily deviation %
        'max_daily_diff': round(daily_diff.abs().max() * 100, 4),  # largest single-day deviation %
        'annualized': annualize
    }


def compare_etfs_same_index(
    etf_codes: list[str],
    index_code: str,
    pro,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Compare the tracking performance of several ETFs on the same index.

    Args:
        etf_codes: list of ETF codes
        index_code: benchmark index code
        pro: tushare pro_api instance
        start_date: start date
        end_date: end date

    Returns:
        DataFrame comparing tracking error across ETFs
    """
    index_df = get_index_daily(pro, index_code, start_date, end_date)
    index_prices = index_df.set_index('trade_date')['close']

    results = []
    for code in etf_codes:
        nav_df = get_etf_nav(pro, code, start_date, end_date)
        etf_prices = nav_df.set_index('end_date')['nav']
        te_result = calc_tracking_error(etf_prices, index_prices)
        te_result['ts_code'] = code
        results.append(te_result)

    return pd.DataFrame(results).set_index('ts_code').sort_values('tracking_error')
```

### 7.3 Premium / Discount Monitoring

```python
def calc_premium_discount(
    market_price: float,
    iopv: float
) -> dict:
    """
    Calculate an ETF's premium/discount and arbitrage signal.

    Args:
        market_price: ETF exchange market price
        iopv: real-time indicative NAV (iNAV / IOPV)

    Returns:
        dict with premium_pct, signal, arbitrage_feasible
    """
    premium_pct = (market_price - iopv) / iopv * 100

    if premium_pct > 0.3:
        signal = 'PREMIUM_HIGH'   # premium: sell the ETF or create shares
        feasible = premium_pct > 0.5  # still profitable after costs?
    elif premium_pct < -0.3:
        signal = 'DISCOUNT_HIGH'  # discount: buy the ETF or redeem shares
        feasible = premium_pct < -0.5
    else:
        signal = 'NORMAL'
        feasible = False

    return {
        'premium_pct': round(premium_pct, 4),
        'signal': signal,
        'arbitrage_feasible': feasible
    }


def monitor_qdii_premium(pro, qdii_codes: list[str], date: str) -> pd.DataFrame:
    """
    Monitor the premium of cross-border ETFs (alert when the premium is too high).

    Args:
        pro: tushare pro_api instance
        qdii_codes: list of cross-border ETF codes
        date: query date 'YYYYMMDD'

    Returns:
        DataFrame of premium and risk level for each cross-border ETF
    """
    results = []
    for code in qdii_codes:
        # Market price
        price_df = pro.fund_daily(ts_code=code, trade_date=date)
        # NAV
        nav_df = pro.fund_nav(ts_code=code, end_date=date)

        if not price_df.empty and not nav_df.empty:
            market_price = price_df.iloc[0]['close']
            nav = nav_df.iloc[0]['nav']
            premium_pct = (market_price - nav) / nav * 100
            risk_level = (
                'HIGH' if premium_pct > 5
                else 'MEDIUM' if premium_pct > 2
                else 'LOW'
            )
            results.append({
                'ts_code': code,
                'market_price': market_price,
                'nav': nav,
                'premium_pct': round(premium_pct, 2),
                'risk_level': risk_level
            })

    return pd.DataFrame(results).sort_values('premium_pct', ascending=False)
```

### 7.4 Fund Flow Analysis

```python
def etf_fund_flow_analysis(
    pro,
    ts_code: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Analyze changes in ETF AUM and net inflows/outflows.

    Args:
        pro: tushare pro_api instance
        ts_code: ETF code
        start_date: start date
        end_date: end date

    Returns:
        DataFrame with AUM changes and estimated fund flows
    """
    nav_df = get_etf_nav(pro, ts_code, start_date, end_date)
    nav_df['end_date'] = pd.to_datetime(nav_df['end_date'])
    nav_df = nav_df.sort_values('end_date')

    # AUM (in units of 100 million)
    nav_df['scale'] = nav_df['unit_nav'] * nav_df['fund_share'] / 1e8

    # AUM change caused by NAV movement (passive)
    nav_df['nav_return'] = nav_df['unit_nav'].pct_change()
    nav_df['passive_change'] = nav_df['scale'].shift(1) * nav_df['nav_return']

    # Net inflow ~ AUM change - passive change from NAV
    nav_df['net_flow'] = nav_df['scale'].diff() - nav_df['passive_change']

    # Period summary
    summary = {
        'total_net_flow': nav_df['net_flow'].sum(),       # total net inflow over the period
        'avg_daily_flow': nav_df['net_flow'].mean(),      # average daily net inflow
        'inflow_days': (nav_df['net_flow'] > 0).sum(),    # days with net inflow
        'outflow_days': (nav_df['net_flow'] < 0).sum(),   # days with net outflow
        'current_scale': nav_df['scale'].iloc[-1]          # latest AUM
    }

    return nav_df[['end_date', 'unit_nav', 'scale', 'net_flow']], summary


def cross_etf_flow_comparison(
    pro,
    etf_codes: list[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Compare fund flows across similar ETFs to gauge investor preference.

    Args:
        pro: tushare pro_api instance
        etf_codes: list of comparable ETF codes
        start_date: start date
        end_date: end date

    Returns:
        DataFrame summarizing and comparing fund flows across ETFs
    """
    rows = []
    for code in etf_codes:
        _, summary = etf_fund_flow_analysis(pro, code, start_date, end_date)
        summary['ts_code'] = code
        rows.append(summary)
    return pd.DataFrame(rows).set_index('ts_code').sort_values('total_net_flow', ascending=False)
```

---

## 8. Common Analysis Scenarios and Prompt Templates

### Scenario 1: Screen for the Best ETF in a Peer Group

```
Analyze all ETFs tracking the [S&P 500 / Russell 2000 / xxx] index.
Dimensions: AUM, expense ratio, 1-year tracking error, average daily dollar volume, bid-ask spread.
Produce a composite score ranking and recommend the best product for [long-term holding / tactical trading / large allocations].
```

### Scenario 2: Sector ETF Rotation Signal

```
Based on [20/60]-day momentum, select the top 3 from the following sector ETFs:
[XLY, XLV, XLK, XLE, XLF, XLI, XLB, XLU]
Also exclude any ETF that has fallen more than 15% over the past 30 days.
```

### Scenario 3: ETF Portfolio Backtest

```
Build the following ETF portfolio and backtest it over [2020-01-01 to 2025-12-31]:
- SPY 40%
- IWM 20%
- IEF 30%
- GLD 10%
Rebalance quarterly; compute annualized return, Sharpe ratio, max drawdown, and correlation with the S&P 500.
```

### Scenario 4: International ETF Premium Monitoring

```
Monitor the real-time premium/discount of the following international ETFs: [EEM, EWJ, INDA]
Alert when the premium exceeds 3% and recommend waiting for it to narrow before entering.
```

---

## 9. Key Points to Watch

1. **Halted or illiquid holdings**: when a sector or country ETF holds many halted names (e.g. Russia-exposed ETFs in 2022), iNAV is distorted and the premium/discount loses meaning
2. **Creation suspensions**: when creations are halted (quota limits, futures position limits), the premium can persist for months and is unsuitable for arbitrage
3. **Index reconstitutions**: the 1~2 weeks around S&P quarterly and Russell June rebalances show recurring patterns
4. **Never hold leveraged ETFs long term**: decay is severe in choppy markets; strictly limit holding periods
5. **T-bill / cash ETFs**: these are money-market substitutes with different logic from ordinary ETFs; liquidity-management tools, not investments
6. **Thinly traded ETFs**: split large orders over several days, use limit orders, and avoid the first and last 15 minutes of the session
7. **Tax treatment**: distributions can be qualified dividends, non-qualified dividends, or return of capital; commodity ETFs may issue K-1s; each is taxed differently from capital gains

---

## China market notes

Mechanics specific to A-share and Hong Kong ETFs that have no direct US equivalent.

**A-share ETF landscape**: broad-market CSI 300 ETF (510300), CSI 500 ETF (510500), ChiNext ETF (159915), STAR 50 ETF (588000); sector ETFs such as consumer (159928), health care (512170), semiconductor (512480), banks (512800); dividend ETF (510880); gold ETF (518880), soybean-meal ETF (159985), crude-oil ETF (162411); treasury ETF (511010), convertible-bond ETF (511380); money-market ETFs (511990, 511880) with T+0 subscription/redemption. Leading managers by AUM: ChinaAMC, E Fund, Huatai-PineBridge, China Southern, Harvest, Bosera. Typical A-share broad-market ETF fees: 0.15% management + 0.05% custody = 0.20%.

**On-exchange ETFs vs off-exchange feeder funds**:

| Dimension | On-exchange ETF | Feeder fund (ETF-linked fund) |
|------|---------|-----------|
| Purchase channel | Brokerage account, real-time trading | Bank / fund direct sales, T+1 subscription and redemption |
| Creation/redemption | In-kind (institutions) or secondary market (individuals) | Cash |
| Premium/discount | Exists (with arbitrage) | None |
| Minimum trade size | 100 units (roughly RMB 10~100) | From RMB 1 |
| Suited to | Tactical trading, large allocations | Periodic investing, small long-term holdings |

**QDII (cross-border) ETFs**: quota limits mean creations are suspended once a manager's QDII quota is exhausted, so the arbitrage mechanism fails and premiums can persist for months; RMB depreciation lifts the NAV of offshore holdings; the A-share close precedes the US open, so IOPV lags. Apply the same 2% / 5% premium warning thresholds. Hedged share classes cost roughly the US-China rate differential (about 1.5~2.5% per year in 2025).

**LOFs and structured funds**: LOFs trade both on and off exchange; the discount arbitrage path is buy on-exchange at a discount, transfer custody (T+2~T+3), redeem off-exchange, with NAV risk during the transfer. Structured (graded) funds with A (fixed-income) and B (leveraged) shares were fully converted to ordinary funds by 2020; the lower-threshold reset mechanism caused heavy B-share losses and premium arbitrage was squeezed.

**CSI index system**: CSI 300 (largest 300 in Shanghai and Shenzhen, with IF futures and 300 options), CSI 500 (next 300~800, mid caps), CSI 1000 (800~1800, small caps), SSE 50 (largest 50 in Shanghai, financials-heavy), ChiNext Index, STAR 50, BSE 50, CSI All Share / Wind All A. CSI 300 and CSI 500 rebalance in June and December each year.

**Thresholds in RMB terms**: AUM < RMB 200M carries closure risk (sustained 90-day average below RMB 50M is a liquidation signal), > RMB 1B is liquid, > RMB 10B is a flagship; average daily turnover > RMB 100M for broad ETFs and > RMB 20M for sector ETFs; the same-index screen drops products under RMB 500M. In-kind creation units are typically 1 million units. Cross-market arbitrage uses IF (CSI 300 index futures) basis; reverse arbitrage requires securities lending.

**Tax**: individual investors pay no capital-gains tax on equity ETFs and cash distributions are tax-free; institutions include capital gains in the 25% corporate income tax, with dividends exempt when held over 12 months. Put high-turnover rotation in individual accounts.

**Data**: Tushare `fund_basic(market='E', status='L')`, `fund_nav`, `fund_daily`, and `index_daily` (e.g. '000300.SH') as shown in Section 7.1; AUM in the fund-flow helper is expressed in RMB 100M units.
