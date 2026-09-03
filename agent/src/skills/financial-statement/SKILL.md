---
name: financial-statement
description: Deep reading of the three financial statements (income statement, balance sheet, cash flow) — cross-statement reconciliation, earnings quality (accruals vs cash flow), DuPont decomposition, and 12 accounting red flags; use when a user asks to analyze a company's financials, earnings quality, or fraud risk.
category: flow
---

# Three-Statement Financial Analysis

## Overview

Starting from the links between the three statements (income statement, balance sheet, cash flow statement), analyze earnings quality in depth, identify signs of accounting manipulation, and decompose the drivers of profitability with DuPont analysis.

## Core Framework for the Three Statements

### Income Statement (how much was earned)

```
Revenue
 - Cost of goods sold                  -> Gross profit (gross margin = gross profit / revenue)
 - SG&A + R&D                          -> Operating income (core profit)
 + Interest & other income / (expense) -> Pre-tax income
 + Non-operating / one-time items      -> Pre-tax income (adjusted view)
 - Income tax                          -> Net income
 - Noncontrolling interest             -> Net income attributable to common shareholders
```

**Key ratios**:

| Ratio | Formula | Healthy Range | Warning |
|------|------|---------|------|
| Gross margin | Gross profit / revenue | Varies widely by industry | Declining 3 consecutive quarters |
| Net margin | Net income / revenue | > 10% is excellent | < 0% with no improving trend |
| Operating expense ratio | (SG&A + R&D) / revenue | < 30% | Rising year after year |
| Core / reported net income | Net income ex one-time items / reported net income (GAAP vs non-GAAP gap) | > 80% | < 50% means reliance on non-recurring items |

### Balance Sheet (what the company owns)

```
Assets = Liabilities + Shareholders' equity

Asset-side focus:
- Cash: is any of it restricted? High cash AND high debt at the same time?
- Accounts receivable: growing faster than revenue?
- Inventory: piling up? Are write-down reserves adequate?
- Goodwill: acquisition premiums, impairment risk
- Construction in progress / capitalized projects: never transferred to fixed assets?

Liability-side focus:
- Interest-bearing debt: short-term borrowings + long-term debt + bonds payable
- Accounts payable: bargaining power over suppliers
- Deferred revenue / contract liabilities: bargaining power over customers
```

**Key ratios**:

| Ratio | Formula | Healthy Range |
|------|------|---------|
| Debt-to-assets | Total liabilities / total assets | 40-60% (non-financial) |
| Current ratio | Current assets / current liabilities | 1.5-2.5 |
| Quick ratio | (Current assets - inventory) / current liabilities | > 1.0 |
| Interest-bearing debt ratio | Interest-bearing debt / total assets | < 30% |

### Cash Flow Statement (how much cash was actually collected)

```
Cash flow from operations (CFO): cash earned by running the business
Cash flow from investing (CFI): cash spent buying / selling assets
Cash flow from financing (CFF): borrowing / repayment / dividends / buybacks

Golden rule: net income ~ CFO (over the long run)
```

**Cash flow quality matrix**:

| CFO | CFI | CFF | Company State |
|-----|-----|-----|---------|
| + | - | - | Excellent (earning, investing, paying down debt / returning capital) |
| + | - | + | Expanding (earning, investing, borrowing to accelerate) |
| + | + | - | Conservative (earning, harvesting investments, repaying debt) |
| - | - | + | Dangerous (losing money, still investing, surviving on borrowed money) |
| - | + | + | Distressed (selling assets and borrowing to stay afloat) |
| - | + | - | Declining (selling assets to repay debt) |

## Links Between the Three Statements

### Core Reconciliations

```
1. Income statement -> balance sheet
   Net income -> retained earnings (increase)
   Increase in receivables = revenue - cash actually collected
   Increase in inventory = purchases - cost of goods sold

2. Income statement -> cash flow statement
   Net income + depreciation - increase in working capital ~ operating cash flow
   Large gap -> earnings quality is questionable

3. Balance sheet -> cash flow statement
   Ending cash = beginning cash + CFO + CFI + CFF
   Change in cash = sum of the three cash flows
```

### Reconciliation Check Formulas

```python
# Check earnings quality
accrual_ratio = (net_income - cfo) / total_assets
# accrual_ratio > 10% -> large accrual component, poor earnings quality

# Check revenue quality
receivable_growth = accounts_receivable.pct_change()
revenue_growth = revenue.pct_change()
# receivable_growth > revenue_growth -> revenue quality deteriorating

# Check balance sheet vs cash flow consistency
cash_change = cash_end - cash_begin
cf_total = cfo + cfi + cff
# abs(cash_change - cf_total) > 1 -> data problem
```

## Earnings Quality Analysis

### Accruals vs Cash Flow

```
High-quality earnings:
- CFO / net income > 1.0 (cash profit exceeds paper profit)
- Receivables growth < revenue growth
- Operating cash flow consistently positive

Low-quality earnings:
- CFO / net income < 0.5 (much of the profit never became cash)
- Receivables / revenue ratio keeps rising
- Reliance on one-time gains (investment income, asset disposals)
```

### Earnings Quality Scorecard

| Metric | Excellent (3) | Average (2) | Poor (1) | Weight |
|------|----------|----------|---------|------|
| CFO / net income | > 1.2 | 0.8-1.2 | < 0.8 | 25% |
| Receivables growth vs revenue | Receivables slower | In line | Receivables faster | 20% |
| Core / reported net income | > 90% | 70-90% | < 70% | 20% |
| Operating cash flow trend | Rising consistently | Volatile | Falling | 20% |
| Inventory turnover | Accelerating | Stable | Slowing | 15% |

Score >= 2.5 = excellent earnings quality
Score 1.5-2.5 = needs attention
Score < 1.5 = poor earnings quality, recommend avoiding

## Accounting Red Flags

### 12 Red-Flag Signals

| # | Red Flag | Detection Method | Severity |
|---|------|---------|--------|
| 1 | High cash and high debt simultaneously | Large cash balance + large interest-bearing debt (both > 30% of revenue) | High |
| 2 | Receivables surge | Receivables growth > 1.5x revenue growth for 2+ consecutive quarters | High |
| 3 | Inventory anomaly | Inventory / revenue ratio suddenly rises > 50% | High |
| 4 | Negative operating cash flow | CFO negative 2 consecutive years while net income is positive | High |
| 5 | Heavy related-party transactions | Related-party transactions / revenue > 30% | High |
| 6 | Frequent auditor changes | Auditor changed twice within 3 years | Medium |
| 7 | Capitalized projects never completed | Construction in progress / fixed assets > 50% for 3+ years | Medium |
| 8 | Prepayment anomaly | Prepayments / revenue ratio suddenly rises | Medium |
| 9 | Noncontrolling interest anomaly | Noncontrolling interest / net income ratio swings widely | Medium |
| 10 | Audit opinion | Non-unqualified opinion (qualified / adverse / disclaimer), going-concern paragraph, or material weakness in internal controls (SOX 404) | High |
| 11 | Excessive capitalization | Capitalized development / software costs / total R&D > 50% | Medium |
| 12 | Goodwill concentration | Goodwill / equity > 30% and acquired businesses missing targets | Medium |

### Overall Manipulation Probability

```
Red flags    Manipulation probability    Recommendation
0-1          Low                         Invest normally
2-3          Medium                      Investigate further, invest cautiously
4-5          High                        Recommend avoiding
6+           Very high                   Strongly avoid
```

## DuPont Analysis

### Three-Factor Decomposition

```
ROE = net margin x asset turnover x equity multiplier

ROE = (net income / revenue) x (revenue / total assets) x (total assets / equity)
      profitability          operating efficiency       leverage
```

### Five-Factor Decomposition

```
ROE = tax burden x interest burden x operating margin x asset turnover x equity multiplier
    = (net income / pre-tax income) x (pre-tax income / EBIT) x (EBIT / revenue) x (revenue / total assets) x (total assets / equity)
```

### DuPont Analysis Template

```markdown
### DuPont Analysis: [Company]

| Metric | 2024 | 2025 | Change | Driver Assessment |
|------|------|------|------|---------|
| ROE | 15.2% | 17.8% | +2.6% | Up |
| Net margin | 8.5% | 9.2% | +0.7% | Profitability improving (ok) |
| Asset turnover | 0.85 | 0.88 | +0.03 | Efficiency improving (ok) |
| Equity multiplier | 2.10 | 2.20 | +0.10 | Leverage rising (watch) |

Conclusion: the ROE improvement is driven mainly by better profitability; the modest rise in leverage needs monitoring
```

### ROE Comparison by Industry

| Industry | Typical ROE | Driver Type |
|------|---------|---------|
| Spirits / tobacco / premium consumer brands | 25-30%+ | High net margin (gross margin > 60-90%) |
| Retail (e.g. WMT, COST) | 8-15% | High turnover (thin margins, high volume) |
| Banks | 10-14% | High leverage (equity multiplier > 10x) |
| Technology (e.g. AAPL, MSFT) | 12-20%+ | High net margin + moderate turnover (buybacks inflate ROE) |
| Real estate / homebuilders | 5-10% | High leverage, but deleveraging |

## Output Format

```markdown
## Financial Analysis: [Company / Ticker]

### Three-Statement Summary
| Metric | 2023A | 2024A | 2025E | Trend |
|------|-------|-------|-------|------|
| Revenue ($M) | ... | ... | ... | ... |
| Net income ($M) | ... | ... | ... | ... |
| CFO ($M) | ... | ... | ... | ... |
| Debt-to-assets | ... | ... | ... | ... |

### Earnings Quality Score
| Metric | Score | Notes |
|------|------|------|
| CFO / net income | 3/3 | 1.25, excellent cash conversion |
| ... | ... | ... |
| **Overall** | **2.7/3** | **Excellent earnings quality** |

### DuPont Decomposition
[DuPont analysis table]

### Red-Flag Check
- [x] High cash and high debt -> No, cash balance is reasonable
- [x] Receivables anomaly -> No, growing slower than revenue
- [!] Goodwill concentration -> 22%, near the warning line, monitor

### Conclusion
...
```

## Points to Watch

1. **Accounting-standard differences**: US filers report under US GAAP, most non-US companies under IFRS, and A-shares under Chinese GAAP; adjust before comparing (e.g. lease treatment, R&D capitalization, revenue recognition)
2. **Compare quarters year-over-year, not sequentially**: seasonality is strong (e.g. holiday-quarter retail), so quarter-over-quarter swings do not indicate a trend
3. **Banks and insurers are special**: their statements are structured completely differently and the standard reconciliation analysis does not apply
4. **Asset-heavy vs asset-light**: asset turnover is not comparable across industries; only peer comparisons are meaningful
5. **Changes in consolidation scope**: newly acquired or divested subsidiaries make year-over-year figures non-comparable; use like-for-like data
6. **Data sources**: `get_financial_statements` returns statement data for US and A-share tickers; SEC 10-K / 10-Q filings are available through the `edgar-sec-filings` skill; valuation fields such as pe / pb / roe come from `get_fundamentals`

## China market notes

- **Chinese GAAP income statement ordering**: investment income and fair-value changes sit inside operating profit, followed by non-operating income/expense to reach total profit; "core profit" (revenue - COGS - taxes and surcharges - selling, G&A and R&D expenses) is the standard operating measure
- **Attributable and recurring earnings**: A-share disclosures separate net income attributable to the parent (guimu) from net income after deducting non-recurring items (koufei); the koufei / guimu ratio is the A-share version of the core / reported ratio in the tables above
- **"High cash, high debt" cases**: this red flag became prominent after A-share frauds in which reported cash did not exist (e.g. Kangmei Pharmaceutical, 2019); check restricted cash and bank confirmations
- **Audit opinions**: A-share auditors issue standard unqualified, unqualified with emphasis of matter, qualified, adverse, or disclaimer opinions; anything other than standard unqualified is a high-severity flag, and Hong Kong filers follow IFRS / HKFRS
- **Data**: Tushare provides A-share statement data; pe / pb / roe are available via extra_fields; use exchange-suffixed codes such as 600519.SH
