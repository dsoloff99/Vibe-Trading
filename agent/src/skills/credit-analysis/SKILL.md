---
name: credit-analysis
description: "Fixed income and credit analysis: bond pricing, yield curves, duration and DV01, credit ratings, Altman Z-Score, Merton/KMV default probability, credit spreads, ABS/MBS, municipal bonds, and convertible bond floors; use when a user asks about bond valuation, interest-rate risk, default risk, or credit-spread strategies."
category: analysis
---

# Credit Analysis Skill — Fixed Income and Credit

## When to Use

Load this skill first when the user asks about:
- Bond pricing, YTM calculation, duration / convexity analysis
- Corporate credit ratings, default probability estimation
- Credit-spread analysis and trading strategies
- Municipal bonds, ABS / MBS credit assessment
- Interest-rate risk management (DV01, key-rate duration)
- Fixed-income market structure

---

## 1. Credit Analysis Framework

### 1.1 Credit Rating System

#### Issuer Rating vs Issue Rating

| Type | Definition | Rated Entity |
|------|------|----------|
| **Issuer Rating** | Overall repayment capacity of the issuer | Corporations, governments, financial institutions |
| **Issue Rating** | Credit quality of a specific bond | A specific bond, considering collateral, seniority, covenants |

An issue rating can be above or below the issuer rating (depending on the security structure).

#### S&P / Moody's / Fitch Rating Scale

| S&P | Moody's | Fitch | Meaning |
|-----|---------|----------|------|
| AAA | Aaa | AAA | Highest credit quality, minimal default risk |
| AA+/AA/AA- | Aa1/Aa2/Aa3 | AA+/AA/AA- | High quality, very low default risk |
| A+/A/A- | A1/A2/A3 | A+/A/A- | Upper-medium credit quality |
| BBB+/BBB/BBB- | Baa1/Baa2/Baa3 | BBB+/BBB/BBB- | Investment-grade floor (IG / HY boundary) |
| BB+ and below | Ba1 and below | BB+ and below | High yield / speculative grade |
| D | D | D | Default |

> **Reading ratings**: the BBB- / Baa3 line drives forced selling by IG-only mandates ("fallen angels"), so watch the outlook (positive / stable / negative) and watch-list status, not just the letter grade.

---

### 1.2 Altman Z-Score Model

Used to predict corporate financial distress; the original model applies to listed manufacturers:

```
Z = 1.2 x X1 + 1.4 x X2 + 3.3 x X3 + 0.6 x X4 + 1.0 x X5
```

| Variable | Formula | Meaning |
|------|----------|------|
| X1 | Working capital / total assets | Liquidity |
| X2 | Retained earnings / total assets | Accumulated profitability |
| X3 | EBIT / total assets | Earning power |
| X4 | Market value of equity / book value of total liabilities | Financial leverage |
| X5 | Sales / total assets | Asset efficiency |

**Decision zones**:
- Z > 2.99: safe zone (low default risk)
- 1.81 < Z < 2.99: grey zone (needs deeper analysis)
- Z < 1.81: distress zone (high default risk)

**Variants**:
- Z' (private companies): X4 uses book value of equity; cut-offs 2.90 / 1.23
- Z'' (non-manufacturers / emerging markets): drops X5; cut-offs 2.60 / 1.10

**Limitations**:
- Based on historical data, so it lags
- Not applicable to financial companies (leverage is defined differently)
- Parameters should be recalibrated for non-US markets

---

### 1.3 Merton Structural Model

Treats the firm's equity as a call option on the firm's assets (strike = face value of debt):

**Core assumptions**:
- Firm asset value V follows geometric Brownian motion: `dV = mu V dt + sigma_V V dW`
- Debt is a zero-coupon bond with face value D maturing at T
- Default occurs only at T (European-style default)

**Equity valuation (Black-Scholes)**:
```
E = V*N(d1) - D*e^(-rT)*N(d2)

d1 = [ln(V/D) + (r + sigma_V^2/2)T] / (sigma_V*sqrt(T))
d2 = d1 - sigma_V*sqrt(T)
```

**Default probability (risk-neutral)**:
```
PD = N(-d2)
```

**Distance to default (DD)**:
```
DD = [ln(V/D) + (mu - sigma_V^2/2)T] / (sigma_V*sqrt(T))
```

**Credit-spread estimate**:
```
Credit spread ~ -ln[N(d2) + (V/D*e^(rT))*N(-d1)] / T
```

**Parameter estimation** (simultaneous equations):
1. E = V*N(d1) - D*e^(-rT)*N(d2)
2. sigma_E*E = N(d1)*sigma_V*V

---

### 1.4 KMV Model (Expected Default Frequency, EDF)

KMV is the commercial implementation of the Merton model, acquired by Moody's:

**Steps**:
1. Back out asset value V and asset volatility sigma_V from the stock price and equity volatility
2. Compute the default point: `DP = short-term debt + 0.5 x long-term debt`
3. Compute distance to default: `DD = (V - DP) / (V x sigma_V)`
4. Map DD to EDF using a historical default database (non-normal mapping)

**Differences from Merton**:
- The default point is not total debt but short-term plus half of long-term debt
- The DD-to-EDF mapping is empirical, not based on a normal distribution
- EDF is a real-world probability, not a risk-neutral one

**EDF reference bands** (approximate):
- EDF < 0.1%: investment grade
- 0.1%-1%: BBB-BB
- 1%-5%: B
- EDF > 5%: CCC and below

---

### 1.5 Credit Scorecard Methodology

Applies to consumer credit / ABS collateral analysis:

**Modeling workflow**:
1. **Data preparation**: collect historical loan data, define the default label (e.g. 90+ days past due)
2. **Feature engineering**: WOE (Weight of Evidence) encoding
3. **Feature selection**: screen by IV (Information Value), keep IV > 0.02
4. **Model training**: logistic regression (mainstream), XGBoost
5. **Score scaling**: `Score = A - B x ln(odds)`, typically base score 600, PDO = 20

**WOE and IV calculation**:
```python
WOE_i = ln(good_share_i / bad_share_i)
IV_i = (good_share_i - bad_share_i) x WOE_i
Total IV = sum(IV_i)
```

**IV reference scale**:
- IV < 0.02: no predictive power
- 0.02-0.1: weak
- 0.1-0.3: medium
- IV > 0.3: strong

---

## 2. Fixed-Income Product Analysis

### 2.1 Treasuries and Government Bonds

#### Yield Curve Analysis

**Spot (zero) curve**: risk-free zero-coupon yields at each maturity, bootstrapped from coupon bonds.

**Forward curve**:
```
f(T1, T2) = [(1+r2)^T2 / (1+r1)^T1]^(1/(T2-T1)) - 1
```

**Term spreads**:
- 10Y-2Y: business-cycle indicator; a negative value usually precedes a recession
- 10Y-3M: the Fed's preferred recession-probability input
- 30Y-10Y: gauge of long-end supply and demand

**Yield curve shapes**:
| Shape | Feature | Economic Meaning |
|------|------|----------|
| Normal (upward sloping) | Long end > short end | Expansion expected |
| Flat | Similar across maturities | Turning point |
| Inverted | Short end > long end | Recession signal |
| Humped | Belly highest | Liquidity segmentation |

#### US Treasury Curve Characteristics
- Benchmark curve: on-the-run Treasuries (bills, notes, bonds) plus the SOFR swap curve
- Key tenors: 3M / 2Y / 5Y / 7Y / 10Y / 30Y
- The 10Y Treasury is the core benchmark rate; agency (Fannie / Freddie) debt trades at a small spread over Treasuries

---

### 2.2 Corporate Bond Analysis

#### Core Metrics

**Coupon rate**: fixed at issuance, paid on face value.

**Yield to maturity (YTM)**:
The internal rate of return that sets bond present value = market price:
```
P = sum [C/(1+y)^t] + F/(1+y)^n
```
where C = coupon, F = face value, y = YTM, n = number of periods.

**Current yield**: `CY = annual coupon / market price` (ignores principal gain / loss)

**Modified duration**:
```
MD = -dP/P / dy = Macaulay Duration / (1+y/m)
```
Meaning: for a 1% change in rates, the bond price moves about MD% (in the opposite direction).

**Convexity**:
```
CX = [sum t(t+1)*CF_t/(1+y)^(t+2)] / P
Price-change correction: dP/P ~ -MD*dy + 0.5*CX*(dy)^2
```

#### Bond Price Formula (Implementation)

The pricing function is tested code in the repository; import it directly and **do not rewrite it in the session**:

```python
from src.quantlib.fixedincome import bond_price

bond_price(face=100, coupon_rate=0.05, ytm=0.04, n_periods=5, freq=1)
# -> 104.4518...   5-year, 5% coupon, YTM = 4%, annual pay
```

Two conventions are **explicit parameters** here, not implicit assumptions:

- `compounding`: `"discrete"` (default, `freq` compounding periods per year, i.e. the `P = sum C/(1+y/m)^t` form above) or `"continuous"`.
- Day count: `bond_price` discounts over whole coupon periods, so it returns the price **on a coupon date** (clean price, accrued = 0).
  For settlement between coupon dates, add accrued interest to get the full (dirty) price:

```python
import datetime as dt
from src.quantlib.fixedincome import accrued_interest

accrued = accrued_interest(
    face=100, coupon_rate=0.05, freq=2,
    last_coupon=dt.date(2024, 1, 15),
    settlement=dt.date(2024, 4, 15),
    next_coupon=dt.date(2024, 7, 15),
    day_count="30/360",   # ACT/365F (default) | ACT/360 | ACT/ACT | 30/360 | 30E/360
)                          # -> 1.25
dirty_price = bond_price(100, 0.05, 0.04, 10, 2) + accrued
```

---

### 2.3 Convertible Bonds (Straight-Debt Component)

> The conversion-option component is covered in the `convertible-bond` skill; this section focuses on the bond floor.

**Bond floor (straight-debt value)**:
```
Bond floor = sum [coupon/(1+r_straight)^t] + face/(1+r_straight)^n
```
where r_straight is the yield on a straight bond of the same rating and maturity.

**Conversion premium and bond-floor premium**:
- Conversion premium = (convertible price - conversion value) / conversion value
- Bond-floor premium = (convertible price - bond floor) / bond floor

**Credit implications of reset and call features**:
Conversion-price resets can dilute shareholders; assess the issuer's incentives (desire to force conversion via soft call vs put pressure from bondholders).

---

### 2.4 ABS / MBS Analysis

#### Collateral Analysis Framework

**Asset-quality metrics**:
- Weighted average coupon (WAC)
- Weighted average maturity (WAM)
- Weighted average loan-to-value (LTV)
- Historical delinquency (DPD 30 / 60 / 90+)
- Cumulative default rate (CDR)

**Prepayment models**:
- CPR (Conditional Prepayment Rate): annualized prepayment rate
- SMM (Single Monthly Mortality): monthly prepayment rate
  ```
  CPR = 1 - (1 - SMM)^12
  SMM = 1 - (1 - CPR)^(1/12)
  ```
- PSA model: standard prepayment assumption (100 PSA = linear ramp to 6% per year over the first 30 months, then constant 6% per year)

**Tranche structure analysis**:
- Senior: paid first, highest rating
- Mezzanine: paid second
- Equity / junior: absorbs first losses, receives excess spread

**Key risk metrics**:
```
Credit enhancement = (collateral pool size - senior tranche size) / senior tranche size
Excess spread = collateral pool yield - senior funding cost - servicing fee
```

---

### 2.5 Municipal Bond Credit Analysis

Municipal bonds (munis) are issued by US states, cities, counties, and their agencies; interest is generally exempt from federal income tax, so they are compared on a tax-equivalent yield basis.

#### Analysis Framework

**Four-dimension assessment model**:

| Dimension | Core Metrics | Weight |
|------|----------|------|
| Economic and fiscal strength | Tax base, general-fund revenue, GDP / employment, reserve ratio | 40% |
| Security type and legal pledge | GO (full faith and credit, taxing power) > essential-service revenue bonds > appropriation-backed > project revenue | 25% |
| Issuer position | Essentiality of the service, monopoly status, diversification of the revenue base | 20% |
| Debt structure | Debt per capita, debt service / revenue, pension and OPEB liabilities, refinancing needs | 15% |

**Stress signals**:
- General-fund reserves / expenditures < 5% (thin liquidity)
- Debt-service coverage ratio < 1.0x on revenue bonds (relying on external funding to pay interest)
- Unfunded pension liabilities > 100% of annual revenue
- Persistent structural deficits, population outflow, single-employer economies

**Muni yield structure** (reference):
```
Muni yield ~ Treasury x (1 - marginal tax rate) + liquidity premium (10-30bp) + credit premium (0-300bp)
Tax-equivalent yield = muni yield / (1 - marginal tax rate)
```

**Policy risk**: after the 2008-2013 stress period (Detroit, Puerto Rico, Chapter 9 filings), watch:
- State oversight and emergency-manager laws
- Pension-reform progress
- Changes to the federal tax exemption or SALT deduction rules

---

## 3. Interest-Rate Risk Management

### 3.1 Duration Framework

#### Macaulay Duration

Present-value-weighted average time to cash flows, in years:
```
D_mac = sum [t x CF_t/(1+y)^t] / P
```

#### Modified Duration

Interest-rate sensitivity measure:
```
D_mod = D_mac / (1 + y/m)
dP ~ -D_mod x P x dy
```

#### Effective Duration

For bonds with embedded options (callables, MBS, etc.):
```
D_eff = (P_down - P_up) / (2 x P_0 x dy)
```
where P_down / P_up are the prices after rates move down / up by dy.

#### Dollar Duration

```
Dollar Duration = D_mod x P x face amount
```

---

### 3.2 Convexity

Measures the sensitivity of duration to rates (second-order effect):

```
C = sum [t(t+1) x CF_t/(1+y)^(t+2)] / P

Refined price estimate:
dP/P ~ -D_mod*dy + 0.5*C*(dy)^2
```

**Value of convexity**: positive convexity makes a bond gain more than expected when rates fall (and lose less than expected when rates rise), so positively convex bonds are preferred to negatively convex ones (callables, MBS).

---

### 3.3 DV01 (Dollar Value of a Basis Point)

Price change for a 1 basis point (0.01%) move in rates:
```
DV01 = D_mod x P x 0.0001
```

Portfolio level: `Portfolio DV01 = sum (DV01_i x position_i)`

**Use**: hedge-ratio calculation
```
Hedge ratio = DV01_position being hedged / DV01_hedging instrument
```

---

### 3.4 Key Rate Duration (KRD)

Measures the price impact of a 1bp move at each key maturity on the curve:
- Common key tenors: 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y
- `KRD_i = -dP/(P x dy_i)` (only the i-th key rate moves 1bp)
- `sum KRD_i ~ D_mod` (key-rate durations sum to approximately the modified duration)

**Applications**:
- Identify portfolio exposure to specific maturities
- Precisely hedge non-parallel shifts (twist / butterfly)

---

### 3.5 Immunization Strategies

**Duration matching**:
Set asset-portfolio duration = liability duration to immunize against parallel shifts.
Condition: `sum (w_i x D_i) = D_liability`

**Cash-flow matching**:
Match each period's cash flow directly, eliminating reinvestment risk, but inflexible and expensive.

**Contingent immunization**:
Manage actively while portfolio value exceeds a safety floor; switch to passive immunization if it falls to the floor.

**Rebalancing frequency**:
- Duration drifts over time, so rebalance periodically (quarterly / monthly)
- Rebalance immediately after a large rate move (> 50bp)

---

## 4. Credit-Spread Analysis

### 4.1 Components of the Credit Spread

```
Credit spread = default-risk premium + liquidity premium + tax premium (some markets)
```

| Component | Drivers | Measurement |
|----------|----------|----------|
| Default-risk premium | Rating, industry, financials, macro cycle | CDS quotes, model estimates |
| Liquidity premium | Issue size, remaining maturity, market depth | Bid-ask spread, turnover |
| Tax premium | Tax exemption on government bonds (some countries / investors) | Yield-differential analysis |

**Spread benchmarks**:
- G-spread (vs Treasuries), I-spread (vs swaps), Z-spread (zero-volatility spread), OAS (option-adjusted spread)
- US practice: IG bonds quoted as a spread to the nearest on-the-run Treasury; HY bonds quoted on price or yield-to-worst

**OAS (Option-Adjusted Spread)**:
Credit spread after stripping out the embedded option value; used to compare bonds with embedded options:
```
P = sum CF_t / (1 + r_t + OAS)^t
```

---

### 4.2 Credit-Spread Curve Shapes

**Upward sloping** (common): long-term spreads > short-term spreads, reflecting accumulating uncertainty over time.

**Flat / inverted**:
- Market is optimistic about long-term credit risk (flat)
- Short-term liquidity crisis / refinancing distress (inverted), a warning signal

**Correlation between credit spreads and Treasury yields**:
- Expansion: spreads tighten (rising risk appetite)
- Recession / credit event: spreads widen
- "Flight to quality": Treasury yields fall while spreads widen, a double hit for high-yield bonds

---

### 4.3 Drivers of Credit-Spread Changes

**Macro factors**:
- GDP growth, PMI: improving expectations -> spreads tighten
- Monetary easing: liquidity premium falls
- Credit events (default waves): systemic spread widening

**Industry factors**:
- Sector policy (e.g. energy regulation, bank capital rules, real-estate cycles)
- Industry cycle
- Refinancing environment

**Issuer-specific factors**:
- Rating actions (downgrade -> spread jumps, especially at the fallen-angel boundary)
- Changes in financial data
- Maturity pressure (approaching maturity -> liquidity premium rises)

---

### 4.4 Credit-Spread Trading Strategies

**Spread tightening trade**:
Long undervalued (wide-spread) credit, short Treasuries to hedge rate risk.
- Suited to: early recovery, Fed easing cycles

**Spread widening trade**:
Short credit (via CDS or HY ETFs such as HYG), long Treasuries.
- Suited to: economic downturn, frequent credit events

**Cross-rating spread trade**:
Long high yield / short investment grade (when spreads are compressing), or the reverse.

**Butterfly spread trade**:
Long the belly, short the short and long ends, capturing relative value in the middle of the credit curve.

**Common US instruments**:
- Single-name CDS and CDX indices (CDX IG / CDX HY): hedge credit risk
- Treasury futures (ZT / ZF / ZN / ZB / UB) and SOFR swaps: hedge duration risk
- Credit ETFs (LQD / HYG / JNK) and TRS: quick beta exposure

---

## 5. Python Implementation (quantlib)

The models in this chapter **are already tested code in the repository**, in `src/quantlib/fixedincome.py` (bond math + curve fitting)
and `src/quantlib/credit.py` (Altman Z / Merton-KMV / spreads). Both modules have matching
`tests/quantlib/test_fixedincome.py` and `tests/quantlib/test_credit.py`; duration and DV01 are verified point by point
against a "reprice at +/-1bp" check.

**Import and call directly; do not rewrite these formulas in the session.** A hand-written copy has no test coverage and is not reproducible.

Unit conventions throughout: rates and ratios are decimals (`0.05` means 5%), maturities and time spans are in **years**,
duration / convexity return values are in **years / years^2** (not coupon periods), and only names with a `_bp` suffix are in basis points.

### 5.1 Bond Pricing, Duration and DV01

```python
from src.quantlib.fixedincome import (
    bond_price, ytm_solve, macaulay_duration, modified_duration,
    convexity, dv01, effective_duration,
)

face, coupon, ytm, n, freq = 100, 0.05, 0.04, 5, 1

price = bond_price(face, coupon, ytm, n, freq)          # 104.4518
ytm_solve(price, face, coupon, n, freq)                 # 0.04 (solve YTM from price)

macaulay_duration(face, coupon, ytm, n, freq)           # 4.5571 years
modified_duration(face, coupon, ytm, n, freq)           # 4.3818 years
convexity(face, coupon, ytm, n, freq)                   # 24.4766 years^2
dv01(face, coupon, ytm, n, freq, par_amount=1_000_000)  # 457.69 dollars per bp
```

**Parameter notes**

| Parameter | Description |
|------|------|
| `freq` | Coupon payments per year, `1` = annual, `2` = semi-annual. Every function accepts it; never hard-code |
| `compounding` | `"discrete"` (default) or `"continuous"`. Under continuous compounding modified duration equals Macaulay duration |
| `par_amount` | Position face value for `dv01`, default 1 million; the market value to hedge is `par_amount * price / face` |
| `bracket` | Root-search interval for `ytm_solve`, default `(-0.5, 10.0)`, covering every tradable bond |

For bonds with embedded options (callables, MBS) the cash flows move with rates, so analytic duration does not apply; use the repricing approach:

```python
d_eff = effective_duration(reprice=lambda y: my_oas_model(y), yield_level=0.04, bump=1e-4)
```

`reprice` must carry its own call / prepayment logic; `effective_duration` only computes `(P_down - P_up) / (2*P_0*dy)`.

### 5.2 Yield Curve Fitting (Nelson-Siegel / Svensson)

```python
import numpy as np
from src.quantlib.fixedincome import fit_yield_curve, nelson_siegel, svensson

maturities = np.array([0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
yields     = np.array([0.019, 0.020, 0.022, 0.024, 0.025, 0.027, 0.028, 0.029, 0.033, 0.035])

fit = fit_yield_curve(maturities, yields, model="svensson")
fit.params      # (beta0, beta1, beta2, beta3, lambda1, lambda2)
fit.rmse        # fit residual (decimal, same unit as the input)
fit(4.5)        # interpolate any maturity -> spot rate at that point
fit([1, 5, 10]) # arrays are accepted too
```

`fit_yield_curve` returns a **`CurveFit` object** (not a `(params, func)` tuple): it is callable
and carries three read-only fields, `model` / `params` / `rmse`. `model` is `"nelson_siegel"` (4 parameters)
or `"svensson"` (6 parameters, two curvature factors).

The fit uses **separable least squares**: given the decay parameters lambda, the betas are linear and solved exactly by OLS,
with only the 1~2 lambdas searched by grid + Nelder-Mead. This matters — a single-start L-BFGS-B over all parameters at once
(what an earlier template in this skill did) **could not even recover a curve it generated itself**:
on a noise-free 10-tenor Nelson-Siegel curve it stopped at RMSE 6.4e-4 (6.4bp),
whereas the current implementation reaches 4.0e-14.

When you need to evaluate the curve directly from parameters (e.g. factor decomposition, scenario simulation), use the underlying functions:

```python
nelson_siegel(tau=[1, 5, 10], beta0=0.045, beta1=-0.02, beta2=0.03, lambda1=2.5)
svensson(tau=5.0, beta0=0.05, beta1=-0.03, beta2=0.04, beta3=-0.02,
         lambda1=1.2, lambda2=8.0)
```

`beta0` is the level factor (long-end asymptotic rate), `beta0 + beta1` is the instantaneous short rate,
`beta2` / `beta3` are curvature factors, and `lambda*` are decay speeds (years). Scalars in, scalars out; arrays in, arrays out.

### 5.3 Altman Z-Score Calculation

```python
from src.quantlib.credit import altman_z_score

z = altman_z_score(
    working_capital=200,      # X1 numerator: current assets - current liabilities
    retained_earnings=300,    # X2 numerator: retained earnings
    ebit=150,                 # X3 numerator: earnings before interest and tax
    equity_value=900,         # X4 numerator: market cap for original, book equity for prime/double_prime
    total_liabilities=600,    # X4 denominator: book value of all liabilities
    total_assets=1000,        # denominator for X1/X2/X3/X5
    revenue=1200,             # X5 numerator; not needed for double_prime, may be omitted
    model="original",         # original | prime | double_prime
)

z.z_score            # 3.255
z.zone               # "safe" | "grey" | "distress"
z.label_zh           # localized zone label string returned by the library
z.components         # {"x1": 0.20, "x2": 0.30, "x3": 0.15, "x4": 1.50, "x5": 1.20}
z.safe_threshold     # 2.99
z.distress_threshold # 1.81
```

The coefficients and cut-offs of the three variants live in `ALTMAN_MODELS` and match the table in section 1.2 one for one:

| `model` | Applies To | Coefficients (X1..X5) | Safe / Distress |
|---------|----------|---------------|-------------|
| `original` | Listed manufacturers (Altman 1968) | 1.2 / 1.4 / 3.3 / 0.6 / 1.0 | > 2.99 / < 1.81 |
| `prime` (Z') | Private companies, X4 uses book equity | 0.717 / 0.847 / 3.107 / 0.420 / 0.998 | > 2.90 / < 1.23 |
| `double_prime` (Z'') | Non-manufacturers / emerging markets, drops X5 | 6.56 / 3.26 / 6.72 / 1.05 / — | > 2.60 / < 1.10 |

> **The X4 denominator is total liabilities, not interest-bearing debt.** The variable table in section 1.2 says "book value of total liabilities",
> and the parameter name `total_liabilities` matches the model definition. Substituting interest-bearing debt systematically overstates Z.

The same financials can land in different zones under the three variants (in the example above: `original` safe, `prime` grey);
that is the point of recalibration, not a contradiction.

### 5.4 Credit-Spread Analysis

```python
from src.quantlib.credit import credit_spread_analysis, spread_term_structure

df = credit_spread_analysis(
    bond_yields=bond_ytm_series,       # pd.Series indexed by date
    risk_free_yields=ust_ytm_series,   # must share the same index as above
    window=252,                        # rolling window (trading days)
    lookback_periods=21,               # lookback for the slow-change column
    signal_z=1.5,                      # |z| threshold that triggers rich/cheap
    input_unit="percent",              # percent | decimal | bp
)
```

The returned DataFrame always has the columns `spread_bp`, `rolling_mean_bp`, `rolling_std_bp`, `z_score`,
`historical_percentile`, `change_1p_bp`, `change_lookback_bp`, `signal`.
`signal` is `"rich"` (spread low, expensive) / `"neutral"` / `"cheap"` (spread high, cheap).

> **`historical_percentile` is a full-sample rank with look-ahead bias and must not be used as a backtest signal.** It ranks each row
> together with the rows **after** it, so the same day's percentile changes as new data arrives (measured: the same row is 0.02 on a
> 50-row slice and 0.01 on 100 rows). This is the original template's behavior, kept so the definition does not change silently.
> `z_score` and `signal` use a rolling window and are causal; use those two for signals.

```python
grid = spread_term_structure(
    issuers={"AAA muni": {1: 0.025, 3: 0.028, 5: 0.032},
             "A muni":   {1: 0.032, 3: 0.041, 5: 0.055}},
    risk_free_curve={1: 0.020, 3: 0.022, 5: 0.025},
    input_unit="decimal",   # note: the default differs from the function above
    decimals=1,
)
# rows = issuers, columns = 1Y_spread_bp / 3Y_spread_bp / 5Y_spread_bp
```

> **Confirm the input unit yourself.** The two functions have different historical defaults: `credit_spread_analysis`
> defaults to yields in **percent** (`3.2` means 3.2%), `spread_term_structure` defaults to **decimal** (`0.032`).
> The defaults preserve the original template's behavior, but `input_unit` is now an explicit parameter — check which kind of series
> you hold before feeding it in; get it backwards and the spread is off by 100x.

### 5.5 Merton Structural Model and KMV

```python
from src.quantlib.credit import (
    merton_model, merton_asset_solve, distance_to_default,
    kmv_default_point, kmv_distance_to_default, edf_reference_band,
)

m = merton_model(
    equity_value=100,   # market value of equity
    equity_vol=0.40,    # annualized equity volatility
    debt_face=100,      # face value of debt (simplified to a single zero-coupon bond)
    risk_free=0.03,     # continuously compounded risk-free rate
    horizon=1.0,        # years to debt maturity
    asset_drift=None,   # asset drift for distance to default; None = use risk_free (risk-neutral)
)

m.asset_value           # 197.04  implied asset value
m.asset_vol             # 0.2030  implied asset volatility
m.distance_to_default   # 3.3868  equals d2 when asset_drift=None
m.default_probability   # 0.000354  risk-neutral default probability N(-d2)
m.credit_spread_bp      # 0.176 bp
```

The simultaneous equations (the two in section 1.3) are solved in `merton_asset_solve`, and they are solved in **log space**,
so the root cannot land on negative asset value or negative volatility; if it fails to converge it raises `ValueError` rather than silently returning garbage.

**Merton DD and KMV DD are two different quantities; do not mix them**:

```python
# Merton: log space, with drift and horizon
distance_to_default(asset_value=200, asset_vol=0.25, default_point=100,
                    horizon=2.0, drift=0.06)

# KMV: linear gap, no horizon or drift; default point = short-term debt + part of long-term debt
dp = kmv_default_point(short_term_debt=100, long_term_debt=200,
                       long_term_weight=0.5)      # -> 200
kmv_distance_to_default(asset_value=1000, asset_vol=0.25, default_point=dp)  # -> 3.2

edf_reference_band(3.2)   # -> (0.001, 0.01), i.e. the 0.1%-1% band in the section 8 table
```

> `edf_reference_band` simply turns the "DD -> EDF" rule-of-thumb table in section 8 into a lookup function.
> Real KMV EDFs come from Moody's proprietary default database; treat this output as an **order-of-magnitude check** only,
> never report it as a calibrated default probability.

**Risk-neutral vs real-world**: `asset_drift` only affects `distance_to_default`, not `d2`,
`default_probability`, or `credit_spread` — the latter three are risk-neutral by definition. For a real-world view,
pass in an expected asset return and then read the band with `edf_reference_band`; do not report `N(-dd)` as an EDF.

---

## 6. US Fixed-Income Market Specifics

### 6.1 Market Structure

#### Dealer (OTC) Market vs Exchange-Traded Products

| Dimension | Dealer / OTC Market | Exchange-Traded (ETFs, futures, listed notes) |
|------|---------------------|--------------------------|
| Regulator | SEC / FINRA (TRACE reporting), Treasury / Fed for government debt | SEC (ETFs), CFTC (futures) |
| Main participants | Banks, dealers, insurers, asset managers, foreign central banks | Retail and institutional investors via brokers |
| Trading method | Request-for-quote, dealer runs, electronic platforms (MarketAxess, Tradeweb) | Central limit order book |
| Main products | Treasuries, agencies, corporates, munis, MBS / ABS | Bond ETFs, Treasury futures, baby bonds |
| Share of volume | ~95% of bond notional | ~5% (but the retail-accessible path) |
| Settlement | T+1 (Treasuries, corporates since 2024) | T+1 |
| Liquidity | High (on-the-run Treasuries) / low (off-the-run corporates, small munis) | High (major ETFs) |

#### Major Bond Types

| Type | Issuer | Regulation / Registration | Credit Risk |
|------|----------|-----------|----------|
| Treasuries (bills / notes / bonds / TIPS) | US Treasury | None | None (sovereign) |
| Municipal bonds (GO / revenue) | States, cities, counties, agencies | MSRB / SEC Rule 15c2-12 | Very low to medium |
| Agency debt and agency MBS | Fannie Mae, Freddie Mac, Ginnie Mae, FHLB | Implicit / explicit federal support | Very low (quasi-sovereign) |
| Certificates of deposit / commercial paper | Banks, corporations | FDIC (CDs) / SEC exempt (CP) | Low |
| Investment-grade corporates | Corporations rated BBB- or better | SEC registration or 144A | Medium |
| High-yield corporates / leveraged loans | Corporations rated BB+ or below | SEC or 144A / private | Medium-high |
| Private credit / direct lending | Non-bank lenders, BDCs | Lightly regulated | Medium-high |
| ABS / CLO / non-agency MBS | SPVs | SEC Reg AB II | Depends on collateral and tranche |

---

### 6.2 Municipal Bond Deep-Dive Points

**Primary-market analysis** (new-issue pricing):
1. Verify the issuer type and legal security (GO vs revenue vs appropriation, state vs local)
2. Review the revenue base (tax revenue vs enterprise revenue such as water, power, toll roads)
3. Assess general-fund balance, reserves, and debt-to-revenue
4. Analyze 3 years of audited financials (ACFR) for one-time transfers and interfund borrowing

**Secondary-market analysis** (portfolio valuation):
1. Track spread changes vs the MMD / AAA muni benchmark curve for the same maturity
2. Watch news flow (missed payments, rating downgrades, pension litigation)
3. Monitor refinancing cadence (maturity wall vs new-issue calendar)
4. Watch state-level policy (oversight boards, bankruptcy eligibility under Chapter 9)

**Warning signals (red lines)**:
- General-fund reserves / expenditures < 5%
- Debt-service coverage < 1.0x on revenue bonds
- Missed or late continuing disclosure filings on EMMA
- Issuer's region losing population and employers
- Management turnover combined with a negative rating outlook

---

### 6.3 Bond Fund and Structured Product Credit Analysis

**Look-through analysis of fund holdings**:
- Balanced / multi-asset funds: assess the equity sleeve (market risk) and fixed-income sleeve (credit risk) separately
- "Core-plus" strategies: 80%+ core bonds, up to 20% high yield / EM / convertibles
- Fund-of-funds and target-date funds: two layers of nesting; assess the underlying funds' holdings

**Liquidity analysis framework**:
```
Fund-level liquidity = f(underlying asset liquidity, redemption terms, amortized-cost vs mark-to-market accounting)
```
- Amortized cost: stable prices but hidden risk (only permitted for government money-market funds)
- Mark-to-market: reflects true value, but visible volatility can trigger redemption runs (e.g. March 2020 bond-fund outflows)

**Steps for assessing underlying credit**:
1. Obtain the bond holdings (quarterly / semi-annual reports, N-PORT filings)
2. Classify by rating / sector / muni vs corporate / securitized
3. Compute the weighted average credit spread
4. Identify concentration risk (single issue > 5% is high concentration)
5. Assess the liquidity ladder (coverage from most to least liquid)

---

### 6.4 Default Case Study Methodology

**Default types**:
| Type | Feature | Typical US Cases |
|------|------|------------|
| Liquidity default | Sound assets but cash flow breaks | Bear Stearns (2008), SVB (2023, bank run) |
| Technical default | Covenant trigger (cross-default / acceleration) | Common among weaker leveraged-loan issuers |
| Operational default | Core business deterioration erodes repayment capacity | Sears (2018), Hertz (2020) |
| Fraudulent default | Accounting fraud / asset stripping | Enron (2001), WorldCom (2002) |

**Precursor signals**:

```
Financial:
  - Receivables / total assets abnormally high (inflated revenue)
  - Large cash balance but a high restricted share
  - Goodwill / intangibles share keeps growing
  - Abnormal share of related-party transactions

Market:
  - Bond price falls persistently (below 90)
  - Credit spread widens rapidly (> 50bp in a week)
  - Lead underwriter changes or declines to participate in new issues
  - CDS quotes (if any) rise sharply

Rating:
  - Placed on negative watch
  - Downgrades by multiple agencies
  - Outlook cut from stable to negative
```

**Post-default analysis framework**:
1. Reconstruct the default trigger timing and cash flows
2. Assess balance-sheet "reality" (real assets vs book assets)
3. Map the priority of claims (guarantees, liens, collateral)
4. Estimate expected recovery rate
5. Trace systemic contagion paths (cross-holdings, similar issuers)

**US recovery-rate references** (Moody's long-run averages):
- Senior secured bank loans: about 60%-80%
- Senior secured bonds: about 50%-60%
- Senior unsecured bonds: about 35%-45%
- Subordinated bonds: about 20%-30%
- Municipal bonds (GO, post-restructuring): historically 60%-100%, but highly case-dependent

---

## 7. Relationship to Other Skills

| Related Skill | Complementary Role |
|------------|----------|
| `convertible-bond` | The conversion-option component is handled by the convertible-bond skill; this skill handles straight-debt pricing and credit risk |
| `macro-analysis` | The macro rate environment and credit-cycle view come from the macro skill |
| `risk-management` | Portfolio-level credit risk (VaR / CVaR) is covered by the risk-management skill |
| `equity-fundamental` | Credit analysis and equity valuation share the financial-statement framework; the Altman Z-Score applies on both sides |

---

## 8. Quick Reference

### Common Formula Cheat Sheet

```
YTM approximation:
  YTM ~ [C + (F-P)/n] / [(F+P)/2]

Duration and price change:
  dP ~ -D_mod x P x dy + 0.5 x CX x P x (dy)^2

DV01 = D_mod x P x 0.0001 x face amount

Credit spread = bond YTM - Treasury YTM at the same maturity

Z-Score risk signals:
  Z > 2.99 -> safe   1.81 < Z < 2.99 -> grey   Z < 1.81 -> distress

Distance to default DD -> EDF:
  DD > 4: EDF < 0.1%
  DD 2-4: EDF 0.1%-1%
  DD 1-2: EDF 1%-5%
  DD < 1: EDF > 5%
```

### US Fixed-Income Data Sources

| Data Type | Recommended Source |
|----------|----------|
| Treasury yield curve | US Treasury daily par curve, FRED (DGS series) |
| Corporate bond prices | FINRA TRACE, Bloomberg, ICE BofA indices (via FRED) |
| Municipal issuer financials | EMMA (MSRB), issuer ACFRs |
| Rating reports | Moody's, S&P Global, Fitch websites |
| Default data | Moody's / S&P annual default studies, Creditsights |
| ABS / MBS data | SEC EDGAR (Reg AB filings), Fannie Mae / Freddie Mac loan-level data |

---

## China market notes

Mechanics specific to the onshore China bond market that have no direct US equivalent.

- **Ratings**: domestic ratings run high; a domestic AA is roughly an international BBB-, so the AA / AA+ / AAA lines matter more than the letter grade suggests and the outlook is essential. Rating agencies: China Chengxin, Lianhe, Golden Credit; default and issuance data on chinamoney.com.cn, Wind, DM; ABS data on CNABS. Altman Z parameters should be recalibrated for A-share issuers.
- **Benchmark curve**: China government bonds (CGBs) plus policy-bank bonds (China Development Bank); key tenors 1Y / 3Y / 5Y / 7Y / 10Y / 30Y; the 10Y CGB is the core benchmark, published by China Central Depository (CCDC) and the Ministry of Finance.
- **Market structure**: the interbank market (CFETS, regulated by the PBoC, ~90% of volume, OTC quotes, DVP T+0/T+1) trades CGBs, policy-bank bonds, NCDs, SCP / CP / MTN registered with NAFMII, and ABS / ABN; the exchange market (SSE / SZSE, regulated by the CSRC, ~10%) trades enterprise bonds (NDRC-approved), corporate bonds of listed companies, and convertibles. Local-government bonds are approved by the Ministry of Finance.
- **LGFV (chengtou) bonds**: bonds of local-government financing vehicles, priced roughly as CGB + liquidity premium (30-50bp) + regional premium (0-200bp) + platform premium (0-100bp). Assess on four dimensions: regional fiscal strength (general public budget revenue, GDP, fiscal self-sufficiency, 40%), platform tier (province > city > county, 25%), platform position (sole platform, asset injections, diversification, 20%), and debt structure (interest-bearing debt, short-term share, refinancing pressure, 15%). Red lines: cash / short-term debt < 0.3 (< 0.5 is tight), non-standard financing / interest-bearing debt > 40%, EBITDA interest coverage < 1, overdue commercial paper on the dishonor list, county-level platforms in regions with debt ratios > 100%, and regional refinancing freezes. Since the 2023 debt-resolution package watch swap progress, platform-to-enterprise transformation, and regional name-list policy. Recoveries after technical defaults have been close to 100%.
- **Wealth-management and asset-management products**: after the shift to NAV-based products, look through mixed products (equity and fixed-income sleeves), "fixed income plus" (80%+ bonds, up to 20% equity / convertibles), and FOF wrappers; amortized-cost accounting is no longer permitted for NAV products; classify holdings by rating / sector / LGFV vs non-LGFV; single-bond concentration > 5% is high.
- **Default history**: liquidity defaults among mid-sized property developers; operational defaults at Yongcheng Coal and Brilliance Auto (2020); fraudulent defaults at Kangmei Pharmaceutical. Recovery references: LGFV near 100%, property developers about 20%-50% (land-bank quality), industrials about 30%-60%, non-bank financials about 40%-70% (depending on regulatory intervention).
- **Hedging tools**: credit risk mitigation warrants (CRMW) and onshore CDS for credit risk; CFFEX treasury futures (TS / TF / T / TL) for duration; credit spreads are typically measured against CGBs or AAA LGFV bonds.
