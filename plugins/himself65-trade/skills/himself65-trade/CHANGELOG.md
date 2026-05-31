# Changelog

## [Unreleased] — kimi-datasource Bridge + Cross-Market Support

### Added

#### New Reference Documentation
- **`references/kimi-datasource-bridge.md`** — Comprehensive operating manual for running the trade skill without Funda AI API access. Covers:
  - Data capability matrix with fallback APIs (`stock_finance_data` → `yahoo_finance`)
  - Market coverage hard limits (`.SH/.SZ/.BJ/.HK/.US` only via `stock_finance_data`; all others via Yahoo Finance)
  - Ticker normalization decision tree for US, HK, China, Korea, Japan, UK, Canada, India, Brazil, Europe
  - Yahoo Finance global ticker format table (`.KS`, `.T`, `.L`, `.TO`, `.NS`, `.SA`, `.DE`, `.PA`)
  - IV proxy methodology using realized volatility from price history
  - Options flow proxy using volume anomaly + sector co-rally + price acceleration
  - Fundamental data integration (segment revenue, margins, holders, peers)
  - 5-step workflow template for 🟡 estimated-data mode
  - 🟢/🟡/🔴 data confidence flag system
  - LEAPS availability by market table (Korea individual stocks = no LEAPS; KOSPI 200 = yes)
  - Cross-market test cases: PENG (US), NVDA (US), SK Hynix (Korea)

#### New Python Tools
- **`references/tools/realized_vol.py`** — Realized volatility and IV Rank proxy calculator
  - Computes 20D, 60D, 1Y annualized realized vol from price history CSV
  - Estimates IV proxy via `realized_vol_60d + 5pp`
  - Computes IV Rank proxy from 1-year rolling 20D vol percentile
  - **Currency auto-detection** from Yahoo Finance CSV `currency` column
  - `--currency` CLI override flag
  - Comma formatting (`KRW 2,333,000.00` instead of `$2333000`)
  - Regime flags (high vol, extreme vol, parabolic)

- **`references/tools/bsm_quick.py`** — Black-Scholes-Merton option pricer
  - Prices calls, computes delta, gamma, theta, vega, rho
  - **Currency support** via `--currency` flag with comma formatting
  - **Adaptive gamma formatting**: scientific notation (`6.82e-08`) for tiny gamma values on high-priced stocks
  - **Theta scaling note**: contextual warning when spot price > 100,000
  - **Adaptive table width**: 110 chars for high-priced stocks vs 100 for normal
  - Automatic LEAPS status classification (`LEAPS_OK` / `MARGINAL` / `SPECULATION`)
  - JSON output mode for programmatic consumption

### Changed

#### `references/strategies.md`
- Added **"When Options Chain Data Is Unavailable (kimi-datasource Mode)"** subsection under LEAPS Stock Replacement
  - Documents 5-step procedure: pull history → compute realized vol → estimate IV → run BSM → find extrinsic boundary
  - Defines adjusted extrinsic thresholds for estimated data:
    - Live chain: < 10%
    - BSM estimate, IV < 60%: < 12% (🟡 flag)
    - BSM estimate, IV > 90%: < 15% (🟡 flag, deep ITM only)
  - Documents critical finding from SK Hynix testing: at 97.8% IV, LEAPS boundary shifts to ~48% ITM — structurally impossible to replace shares at moderate strikes
  - Explicit rule: when BSM says no strike satisfies extrinsic < 10%, the setup is **invalid for stock replacement**

#### `references/pitfalls/21-event-iv-vs-demand-iv.md`
- Rewrote Step 2 from unconditional "Always pull net premium data" to **conditional IF/ELIF/ELSE**:
  - **IF Funda available**: standard net premium flow analysis
  - **ELIF kimi-datasource only (🟡 mode)**: proxy demand-IV from volume anomaly (`current_vol / 30d_avg > 2.0`), sector co-rally (`get_related_stock`), and price acceleration (20D return > +30%)
  - **ELSE**: default to catalyst clock only; state "⚠️ low confidence"
- Added explicit confidence flag requirements for each branch

#### `references/pitfalls/24-capped-upside-vs-bull-conviction.md`
- Added **5 data-driven bonus checks** to bull-conviction count (each +0.5 points, max +2 from bonus):
  - Narrative segment revenue accelerating QoQ (`get_stock_business_segmentation`)
  - Gross margin expanding QoQ (`get_financial_statements`)
  - Operating cash flow > net income (`get_financial_statements`)
  - Top 5 institutional holders increasing positions (`get_holder_info`)
  - 3+ sector peers rallying >+15% (`get_related_stock`)
- Added half-point rationale: prevents fundamentals-only analysis from triggering asymmetry rule without directional market confirmation

### Discovered / Validated via Testing

- **`stock_finance_data` hard limit**: explicitly rejects all suffixes except `.SH`, `.SZ`, `.BJ`, `.HK`, `.US`
- **Yahoo Finance coverage**: successfully tested for Korean stocks (`000660.KS`); returns price history, stock info, and currency metadata
- **LEAPS boundary sensitivity**: at 97.8% IV (SK Hynix), extrinsic < 10% requires ~48% ITM strike — dramatically deeper than at 40% IV
- **Cross-market workflow**: full end-to-end analysis (bootstrap → vol → BSM → recommendation) validated on PENG, NVDA, and SK Hynix

### Known Issues / Future Work

- `bsm_quick.py` uses scipy; on fresh environments without scipy, install via `uv pip install scipy --system`
- Currency display in tools uses ISO codes (KRW, USD) rather than symbols (₩, $) to avoid unicode issues
- Gamma formatting switches to scientific notation at < 0.0001; this threshold is arbitrary and could be made adaptive
- Korean individual stock options lack LEAPS (max 3–6 months); the bridge doc flags this but does not yet provide KOSPI 200 index option analysis templates
