# kimi-datasource Bridge — Trade Skill Operation Without Funda

Operating manual for the trade skill when `kimi-datasource` (via MCP) is the only data provider available. This is a **degraded-data regime** — the analytical framework remains intact, but every recommendation must carry a data-confidence flag.

> ⚠️ **kimi-datasource is a stock and fundamental data engine, not an options data engine.** It provides no options chains, no live Greeks, no IV term structure, and no options flow. The trade skill's standard workflow assumes these are available. This document specifies how to adapt.

---

## 1. Data Capability Matrix

| Trade Skill Need | Primary API | Fallback API | Parameters | Quality | Confidence |
|---|---|---|---|---|---|
| Historical daily prices | `stock_finance_data_get_price` | `yahoo_finance_get_historical_stock_prices` | `ticker`, `start_date`, `end_date`, `file_path` | ✅ Exact | 🟢 |
| Real-time quote | `query_stock` or `stock_finance_data_get_stock_realtime_price` | `yahoo_finance_get_stock_info` | `ticker`, `type=realtime_price`, `file_path` | ✅ Exact | 🟢 |
| Company profile | `stock_finance_data_get_stock_info` | `yahoo_finance_get_stock_info` | `ticker`, `file_path` | ✅ Exact | 🟢 |
| Financial statements (IS/BS/CF) | `stock_finance_data_get_financial_statements` | `yahoo_finance_get_financial_statement` | `ticker`, `statement`, `financial_parameter`, `file_path` | ✅ Exact | 🟢 |
| Segment revenue breakdown | `stock_finance_data_get_stock_business_segmentation` | Web search | `ticker`, `financial_parameter`, `file_path` | ✅ Exact | 🟢 |
| Financial ratios | `stock_finance_data_get_stock_financial_index` | `yahoo_finance_get_stock_info` | `ticker`, `financial_parameter`, `category`, `file_path` | ✅ Exact | 🟢 |
| Shareholder / institutional holdings | `stock_finance_data_get_holder_info` | `yahoo_finance_get_holder_info` | `ticker`, `file_path` | ✅ Exact | 🟢 |
| Thematic / sector peer screen | `stock_finance_data_get_related_stock` | Web search | `stock_keyword`, `market=US_stock`, `file_path` | ✅ Exact | 🟢 |
| **Options chain (strikes, bid/ask, OI)** | **Unavailable** | — | ❌ | 🔴 |
| **Implied volatility by strike / expiry** | **Unavailable** | — | ❌ | 🔴 |
| **Options Greeks (live)** | **Unavailable** | — | ❌ | 🔴 |
| **Net options premium flow** | **Unavailable** | — | ❌ | 🔴 |
| **Short interest** | **Unavailable** | — | ❌ | 🔴 |
| **Earnings calendar (US stocks)** | **Unavailable** | — | ❌ | 🔴 |

**Bottom line**: Price history, fundamentals, and sector context are solid. Everything options-specific must be **proxied or estimated**.

---

## 2. Data Source Selection by Market

`kimi-datasource` has **two distinct data sources** with different market coverage. Choosing the wrong one wastes API calls.

### 2.1 Market Coverage: Hard Limits

| Data Source | Supported Markets | Rejected Markets |
|---|---|---|
| `stock_finance_data` | China A-shares (.SH/.SZ/.BJ), Hong Kong (.HK), US (.US/.O/.N) | **Korea, Japan, UK, Europe, India, Brazil, Canada** |
| `yahoo_finance` | US, Canada, UK, Europe, Japan, Korea, India, Brazil, and others | None known |

**Critical rule**: If `stock_finance_data` returns `PARAMETER_ERROR - No supported stock codes found. Only .SH, .SZ, .BJ, .HK, .US suffixes are supported`, **immediately switch to `yahoo_finance`**. Do not retry with other suffixes.

### 2.2 Decision Tree

```
1. What market is the ticker?
   ├── China / HK / US → Use stock_finance_data (primary) or yahoo_finance (backup)
   ├── Korea (.KS) → Use yahoo_finance ONLY
   ├── Japan (.T) → Use yahoo_finance ONLY
   ├── UK (.L) → Use yahoo_finance ONLY
   ├── Canada (.TO) → Use yahoo_finance ONLY
   └── Unknown → Web search to confirm exchange → route to correct API
```

### 2.3 Ticker Normalization

#### US Stocks (NASDAQ / NYSE)

| API | Required Suffix | Example | Common Error |
|---|---|---|---|
| `get_stock_realtime_price` | `.US` | `PENG.US` | `.O` fails |
| `get_price` | `.O` (NASDAQ) or `.N` (NYSE) | `PENG.O`, `X.N` | `.US` fails with "PARAMETER_ERROR" |
| `get_stock_info` | `.O` or `.N` | `PENG.O` | `.US` may fail |
| `get_financial_statements` | `.O` or `.N` | `PENG.O` | `.US` fails |
| `yahoo_finance` (all endpoints) | No suffix | `AAPL`, `NVDA` | — |

**US retry rule**: If `stock_finance_data` returns suffix errors, alternate between `.US` and `.O`/`.N`.

#### HK Stocks

| API | Suffix | Example |
|---|---|---|
| `stock_finance_data` (all) | `.HK` | `0700.HK`, `0005.HK` |
| `yahoo_finance` | `.HK` | `0700.HK` |

#### A-Shares

| API | Suffix | Example |
|---|---|---|
| `stock_finance_data` (all) | `.SH`, `.SZ`, `.BJ` | `600519.SH`, `000001.SZ` |
| `yahoo_finance` | `.SS` (Shanghai), `.SZ` (Shenzhen) | `600519.SS`, `000001.SZ` |

#### Yahoo Finance — Global Ticker Formats

| Market | Yahoo Suffix | Example | Notes |
|---|---|---|---|
| Korea (KRX) | `.KS` | `000660.KS` | Individual stocks |
| Japan (TSE) | `.T` | `7203.T` | Toyota |
| UK (LSE) | `.L` | `BP.L` | — |
| Canada (TSX) | `.TO` | `ENB.TO` | — |
| India (NSE) | `.NS` | `RELIANCE.NS` | — |
| Brazil (Bovespa) | `.SA` | `PETR4.SA` | — |
| Germany | `.DE` | `SAP.DE` | — |
| France | `.PA` | `AIR.PA` | — |

**Always verify ticker format on finance.yahoo.com before API call.**

---

## 3. Proxy Methodology — When Options Data Is Missing

### 3.1 IV Proxy: Realized Volatility

Since live IV is unavailable, compute **realized vol** from price history and use it as a baseline.

```python
import pandas as pd
import numpy as np

df = pd.read_csv('/tmp/TICKER_history.csv')
df['returns'] = df['close'].pct_change()

realized_vol_20d = df['returns'].tail(20).std() * np.sqrt(252)
realized_vol_60d = df['returns'].tail(60).std() * np.sqrt(252)
realized_vol_1y  = df['returns'].tail(252).std() * np.sqrt(252)
```

**IV estimation rules**:

| Scenario | Estimated IV | Confidence |
|---|---|---|
| No options data at all | `realized_vol_60d + 5pp` | 🟡 Low |
| Post-earnings, vol spike fading | `realized_vol_20d` | 🟡 Medium |
| Sustained trending stock | `max(realized_vol_20d, realized_vol_60d)` | 🟡 Medium |
| Vol compression suspected | `realized_vol_20d` (most recent) | 🟡 Medium |

**IV Rank proxy**: Compute a 1-year rolling 20-day realized vol series. Your current `realized_vol_20d` percentile within that series is your **IV Rank proxy**.

> **Honesty requirement**: Every recommendation using IV proxy must state:  
> *"IV estimated from realized volatility. Actual market IV may differ ±15–30 percentage points. Greeks and breakevens are approximate."*

### 3.2 Options Price Proxy: BSM Estimation

When no options chain is available, use the Black-Scholes estimator (see `../tools/bsm_quick.py`) to approximate premiums, deltas, and extrinsic percentages.

**Critical use cases**:
- LEAPS stock replacement: verify `extrinsic < 10%` of premium
- Counterfactual P/L matrices: compute breakevens at different strikes
- Structure comparison: compare bull call spread debit vs. pure long call cost

**Accuracy expectation**: ±10–20% vs. live market prices due to bid-ask spreads, skew, and dividend assumptions.

### 3.3 Options Flow Proxy: Price-Volume + Sector Confluence

Since net options premium flow is unavailable, infer demand-driven vs. event-driven IV from:

| Proxy Signal | Data Source | Threshold |
|---|---|---|
| Volume anomaly | `get_price` → `volume` vs. 30-day average | `current_volume / 30d_avg > 2.0` |
| Price acceleration | `get_price` → 20-day return | `> +30%` in 20 sessions |
| Sector co-rally | `get_related_stock` with thematic keyword | 3+ peers also rallying >+20% in past month |
| Earnings proximity | Web search | < 14 days = event-driven default; > 45 days = demand-driven default |

**Classification rule**:
- IF (`volume > 2x avg` AND `sector peers rallying` AND `earnings > 30 days away`) → **demand-driven IV** → do NOT assume IV crush
- IF (`volume normal` AND `earnings < 14 days`) → **event-driven IV** → crush likely post-earnings
- OTHERWISE → **mixed / uncertain** → state assumption gap explicitly

---

## 4. Fundamental Data Integration

`kimi-datasource` provides financial data that the base trade skill under-utilizes. Incorporate these into the **bull-conviction count** and thesis validation.

### 4.1 Segment Narrative Validation

**API**: `stock_finance_data_get_stock_business_segmentation`

Use this to verify that the segment driving the investment thesis is actually growing:

| Check | How to Validate |
|---|---|
| Narrative segment revenue accelerating | Compare latest segment revenue YoY vs. prior quarter |
| Narrative segment margin expanding | Segment gross profit / segment revenue, QoQ trend |
| Legacy segment shrinking appropriately | Confirm decline is expected, not a red flag |

**Example**: For PENG, the thesis is "Advanced Computing / AI infra." The segment data would reveal whether that segment's revenue is growing and whether the "Optimized LED" drag is priced in.

### 4.2 Earnings Quality Checks

**API**: `stock_finance_data_get_financial_statements`

| Check | Statement | Field | Red Flag |
|---|---|---|---|
| Revenue vs. EPS divergence | Income Statement | `total_revenue` vs. `net_income` | Revenue declining while EPS beats = margin extraction, not growth |
| Cash flow coverage | Cash Flow | `operating_cash_flow` | OCF << net income = low earnings quality |
| Balance sheet stress | Balance Sheet | `total_liabilities` / `total_equity` | Rising leverage during a growth narrative = hidden risk |

### 4.3 Institutional Context

**API**: `stock_finance_data_get_holder_info`

| Check | Signal |
|---|---|
| Top 10 holders increasing positions | +1 conviction (smart money accumulation) |
| New institutional holder appearing in top 10 | +1 conviction (fresh capital) |
| Top holder reducing >20% | -1 conviction (distribution warning) |

---

## 5. Workflow Template — kimi-datasource Mode

Use this sequence for every trade analysis when operating without Funda.

### Step 1: Session Bootstrap (5 min)
1. Confirm ticker + exchange via web search
2. Normalize ticker suffix per Section 2
3. Pull price history (`get_price`, 2–3 years)
4. Pull real-time quote (`query_stock`)

### Step 2: Fundamental Context (10 min)
5. Pull latest income statement (`get_financial_statements`)
6. Pull segment breakdown (`get_stock_business_segmentation`)
7. Pull holder info (`get_holder_info`)
8. Pull sector peers (`get_related_stock` with thematic keyword)
9. Web search for earnings date and recent catalysts

### Step 3: Volatility & Regime Diagnosis (10 min)
10. Compute realized vol from price history (`tools/realized_vol.py`)
11. Estimate IV proxy per Section 3.1
12. Compute IV Rank proxy from rolling realized vol
13. Assess demand-driven vs. event-driven per Section 3.3

### Step 4: Structure Analysis (15 min)
14. Run BSM estimator for candidate strikes (`tools/bsm_quick.py`)
15. Verify LEAPS stock-replacement conditions if applicable
16. Build counterfactual P/L matrix
17. Run Monte Carlo for probability assessment (`tools/mc-probability.py`)

### Step 5: Recommendation (5 min)
18. Pick structure per `strategies.md` regime table
19. Attach data-confidence flag per Section 6
20. State explicit thesis precondition and exit plan

**Total time**: ~45 minutes for a complete analysis.

---

## 6. Data Confidence Flags

Every recommendation must carry one of three flags:

| Flag | Meaning | When to Use |
|---|---|---|
| 🟢 **Live data** | Options chain pulled. IV/Greeks verified. Flow data checked. | Funda or equivalent available |
| 🟡 **Estimated data** | Options prices from BSM. IV from realized vol proxy. Flow from price/volume. | kimi-datasource only (standard mode) |
| 🔴 **Blind** | No price history, no fundamentals, no vol estimate. Thesis based purely on news / opinion. | Emergency only; avoid if possible |

**Flag attachment rule**: The confidence flag must appear in the first paragraph of any recommendation and in the summary table.

> **Example**:  
> 🟡 *This analysis operates in estimated-data mode. Options prices are BSM approximations. IV is proxied from 60-day realized vol. Flow is inferred from volume and sector moves. Actual market prices may differ ±10–20%.*

---

## 7. Cross-Reference Map

| This Document Section | Modifies / Enables |
|---|---|
| Section 3.1 (IV Proxy) | `pitfalls/19.md`, `pitfalls/21.md` — regime classification without live IV |
| Section 3.2 (BSM Proxy) | `strategies.md` — LEAPS validation, counterfactual P/L matrices |
| Section 3.3 (Flow Proxy) | `pitfalls/21.md` — demand-driven vs. event-driven IV without flow data |
| Section 4 (Fundamental Integration) | `pitfalls/24.md` — additional bull-conviction inputs |
| Section 5 (Workflow) | All reference files — standardizes agent behavior |
| Section 6 (Confidence Flags) | All output — prevents false precision |

---

## 8. Yahoo Finance — Options Chain Exploration

`kimi-datasource` also exposes a `yahoo_finance` API. Per the skill description, it supports **"AAPL 期权链"** (options chain). This is **untested** in the trade skill context.

**Recommended protocol**:
1. During session bootstrap, query `yahoo_finance` options data for the ticker
2. If options chain is returned: use it for strike list, volume, and OI
3. If Greeks are returned: treat as 🟡 unverified (Yahoo Greeks are often delayed / smoothed)
4. If no options data is returned: fall back to BSM proxy entirely

Do **not** block analysis waiting for Yahoo Finance to work. It is a bonus, not a dependency.

---

## 9. Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| No live bid-ask spreads | BSM estimates ignore liquidity premium | Widen estimates by ±10% for OTM, ±5% for ITM |
| No term structure (weekly vs. monthly IV) | Cannot diagnose calendar/diagonal opportunities | Avoid calendar/diagonal recommendations in 🟡 mode |
| No 0DTE / weekly options data | Cannot analyze gamma squeeze / pinning | Refer to `gamma-framework.md` conceptually only |
| No borrow cost data | Cannot assess hard-to-borrow risk for short structures | Avoid naked short structures in 🟡 mode |
| `get_price` max 3 years | Cannot compute multi-cycle vol history | Use available window; state limitation |
| `query_stock` max 3 tickers | Cannot batch-screen watchlists | Process in groups of 3 |
| **LEAPS not available for all markets** | Korean individual stocks max 3–6 months; HK limited to 6–9 months | Verify expiry availability before analysis; use index options or ADRs if needed |
| **Currency mismatch across APIs** | `stock_finance_data` and `yahoo_finance` use different suffixes for same market (e.g., `.SH` vs `.SS`) | Verify ticker format per API table in Section 2 |

### LEAPS Availability by Market

| Market / Exchange | LEAPS Available? | Typical Max Expiry | Fallback for Long-Dated Exposure |
|---|---|---|---|
| US (NYSE/NASDAQ) | ✅ Yes | 2–3 years | — |
| US Indices (SPX, NDX) | ✅ Yes | 2–3 years | — |
| HK (HKEX) individual stocks | ⚠️ Limited | 6–9 months | HSCEI / HSI index options |
| Korea (KRX) individual stocks | ❌ No | 3–6 months | KOSPI 200 index options; US-listed ADR if available |
| Korea (KRX) KOSPI 200 index | ✅ Yes | 6–12 months | — |
| Japan (TSE) individual stocks | ⚠️ Limited | 6 months | Nikkei 225 index options |
| Europe (Eurex, LIFFE) | ⚠️ Limited | 6–12 months | Euro Stoxx 50 index options |

**Rule**: Before analyzing "LEAPS" on a non-US ticker, verify options expiry availability. If LEAPS do not exist, switch analysis to:
- Shorter-dated options (3–6 months)
- Index options with correlation to the stock
- US-listed ADR options (if ADR exists)
- Single-stock futures (if available)

## 10. Testing This Bridge

### Test Case 1: PENG (US NASDAQ) — Canonical Baseline

1. Normalize ticker: `PENG.US` (realtime) / `PENG.O` (historical)
2. Pull 2-year price history via `stock_finance_data_get_price`
3. Compute realized vol: expect ~72–78%
4. Estimate IV proxy: ~77–83%
5. Run BSM for Jan 2027 strikes: verify $25 strike extrinsic ≈ 10%
6. Build P/L matrix for $60/$70/$80 calls
7. Attach 🟡 flag to recommendation

**Pass criteria**: Coherent, quantified output with honest uncertainty flags.

### Test Case 2: 000660.KS (SK Hynix, Korea) — Cross-Market Stress Test

1. **Verify API routing**: `stock_finance_data` rejects `.KS` → switch to `yahoo_finance`
2. Pull 2-year history via `yahoo_finance_get_historical_stock_prices` with ticker `000660.KS`
3. Run `realized_vol.py`: verify auto-detects `KRW` currency from CSV
4. Verify output shows `KRW 2,333,000.00` (not `$2,333,000`)
5. Run `bsm_quick.py --currency KRW`: verify comma formatting and scientific gamma
6. Verify LEAPS boundary is extremely deep ITM (extrinsic < 10% only at ~50% ITM due to 97% IV)
7. **Verify market structure limitation**: Korean individual stocks have no LEAPS → max 3–6 month expiry
8. Attach 🟡 flag with cross-market disclaimer

**Pass criteria**: Tools handle non-US currency, high nominal prices, scientific gamma notation, and flag market-specific limitations.

### Test Case 3: NVDA (US Mega-Cap) — Moderate Vol Regime

1. Pull history via `stock_finance_data` or `yahoo_finance`
2. Compute realized vol: expect ~35–40%
3. Run BSM: verify LEAPS boundary exists (unlike SK Hynix)
4. Confirm post-earnings IV compression is detectable

**Pass criteria**: Distinguishes peak-vol regime (SK Hynix, PENG) from moderate-vol regime (NVDA).
