# Trade

Multi-leg options trading assistant — concrete strikes, IV-aware structures, probability-weighted scenarios. Primarily US-equity, with cross-market support via kimi-datasource (Yahoo Finance) for Korea, Japan, UK, Canada, India, Brazil, and Europe. Backed by a curated library of 24 pitfalls and 8 closed-trade case studies (INTC, Mag-7, APP, NOK, TSEM, CBRS, SNOW).

## Triggers

- Trade analysis requests, options strategy recommendations, post-mortems
- Mentions of multi-leg structures: Jade Lizard, bull put / bear call spread, iron condor, diagonal, calendar
- Earnings positioning, IV / IV crush, channel checks, AH price action
- Any single-stock options play in a US-equity context

See the full trigger list in the `description` field of `SKILL.md`.

## Platform

**CLI / Kimi Code** — uses `finance-data-providers:funda-data` (primary) for full options chain + flow data, or `kimi-datasource` (fallback) via Yahoo Finance for price history + fundamentals when Funda is unavailable or the ticker is outside US/HK/CN coverage.

## Setup

### Primary mode (Funda AI API — full options data)
1. Install the [`finance-skills`](https://github.com/himself65/finance-skills) plugin marketplace and the `finance-data-providers:funda-data` skill.
2. Set the Funda API key:
   ```bash
   export FUNDA_API_KEY="your-funda-api-key"
   ```
   or add to `.env` at the repo root (the skill reads `.env` from the git root so worktrees inherit the key).

### Fallback mode (kimi-datasource — price history + fundamentals only)
1. Ensure the `kimi-datasource` plugin is installed (bundled with kimi-code).
2. No additional API key needed — uses Yahoo Finance public endpoints.
3. Install Python dependencies for the bridge tools:
   ```bash
   uv pip install scipy --system
   ```
4. See `references/kimi-datasource-bridge.md` for the full protocol, ticker formats, and confidence-flag system.

## Reference Files

| File | Description |
|---|---|
| `references/strategies.md` | Structure-to-regime matching, setup checklist, position management |
| `references/gamma-framework.md` | Dealer GEX + options chain + IV term + flow → multi-factor probability map |
| `references/price-action-framework.md` | Orderbook microstructure mental model |
| `references/pitfalls/README.md` | Index of 24 trading pitfalls (severity-tagged, lookup-by-trade-type) |
| `references/pitfalls/NN-*.md` | One file per pitfall — read only when relevant |
| `references/ticker/README.md` | Index of closed trade case studies |
| `references/ticker/<name>.md` | One file per case study (INTC Apr 2026, Mag-7 Q1 2026, APP May 2026, NOK, TSEM, CBRS, SNOW) |
| `references/kimi-datasource-bridge.md` | Operating manual for degraded-data regime (no Funda API) |
| `references/tools/realized_vol.py` | Realized volatility + IV Rank proxy calculator |
| `references/tools/bsm_quick.py` | Black-Scholes-Merton option pricer |

## Coverage

- **24 analytical pitfalls** covering consensus anchoring, flow misreading, IV crush traps, T+1 reverse drift, LEAPS vega tax, manipulator-tape recognition, channel-check sample bias, AH order-book fades, event-IV vs demand-IV, capped-upside asymmetry, and more.
- **8 detailed case studies** showing thesis evolution, structure selection, and post-mortem lessons (INTC, Mag-7, APP, NOK, TSEM, CBRS, SNOW).
- **Structure-to-regime quick reference** covering high/low IV regimes paired with directional / neutral / manipulator-tape views.
- **kimi-datasource bridge** for running analysis without Funda AI API — includes IV proxy methodology, options flow proxy, cross-market ticker formats, and 🟡 estimated-data confidence flags.
