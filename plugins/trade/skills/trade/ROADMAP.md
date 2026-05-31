# Roadmap — himself65 Trade Skills for Kimi

> Last updated: 2026-05-30
> Status: Phase 1 complete. Phase 2 ready to start.

---

## Phase 1: "Stop the Bleed" ✅ COMPLETE

**Goal:** Make the skill functional for LEAPS analysis without Funda API.

**Original scope:** bridge.md, realized_vol.py, bsm_quick.py, strategies.md, pitfalls/21.md

**What actually shipped:**

| Item | Status | Notes |
|------|--------|-------|
| `references/kimi-datasource-bridge.md` | ✅ | 277-line operating manual. Data capability matrix, ticker formats, IV proxy protocol, options flow proxy, 🟡 confidence-flag system, LEAPS-by-market table |
| `references/tools/realized_vol.py` | ✅ | RV/IV-rank calculator. Auto-detects currency from Yahoo CSV. Comma formatting. Regime flags |
| `references/tools/bsm_quick.py` | ✅ | BSM pricer. Currency support. Adaptive gamma (scientific notation). Theta scaling note. JSON output |
| `references/strategies.md` | ✅ | LEAPS proxy protocol. Adjusted extrinsic thresholds (<12% for IV<60%, <15% for IV>90%). Critical finding: at 97.8% IV, boundary shifts to ~48% ITM |
| `references/pitfalls/21-event-iv-vs-demand-iv.md` | ✅ | Conditional IF/ELIF/ELSE: Funda → net premium flow; kimi-datasource → volume anomaly + sector co-rally + price acceleration |
| `references/pitfalls/24-capped-upside-vs-bull-conviction.md` | ✅ | 5 data-driven bonus checks (+0.5 each, max +2). Prevents fundamentals-only analysis from triggering asymmetry rule without market confirmation |
| `SKILL.md` + `README.md` | ✅ | **Bonus (was 1.4a)**. Cross-market description, dual-mode data access, confidence flags, language fix, tool references |

**Validated on:** PENG (US), NVDA (US), SK Hynix 000660.KS (Korea)

**Key discovery:** `stock_finance_data` rejects all suffixes except `.SH/.SZ/.BJ/.HK/.US`. Yahoo Finance is the sole viable fallback for non-US/HK/CN markets. Korean individual stocks lack LEAPS entirely (max 3–6 month options).

---

## Phase 2: "Honest Probabilities" 🔄 READY

**Goal:** Answer "what are the odds?" with rigor.

| Item | Priority | Why | Complexity |
|------|----------|-----|------------|
| `references/tools/mc-probability.py` | **P0** | Depends on bsm_quick.py outputs. Monte Carlo price-path simulation → probability of profit, probability of touching, probability of max loss. Replaces gut-feel "base/bull/bear" with quantified percentiles. | Medium |
| `references/tools/ticker_normalize.py` | P1 | Auto-detect market from ticker string and normalize to Yahoo Finance format. Eliminates manual ticker lookup. Polish after core works. | Low |
| Test Yahoo Finance `get_option_chain` | P1 | API docs say it exists and is US-only. If it works, eliminates BSM proxy for US stocks. If it fails, confirms BSM is the only path. | Low |
| Update `references/pitfalls/24.md` with MC integration | P2 | Once mc-probability.py exists, update bull-conviction P/L matrix to use MC-derived probabilities instead of static scenarios | Low |

**Expected output:** Agent can quote "35% probability of max profit, 18% probability of touch, 47% probability of loss" for any LEAPS or multi-leg structure, in both 🟢 Funda and 🟡 estimated modes.

---

## Phase 3: "Workflow & Depth" 📋 PLANNED

**Goal:** Standardize, enrich, and polish.

| Item | Priority | Why | Complexity |
|------|----------|-----|------------|
| `references/tools/trade-skill-init.sh` | P1 | One-command bootstrap: check deps (scipy), validate Funda key, validate kimi-datasource, run self-test on a known ticker. Only useful once all tools are stable. | Medium |
| Fundamental integration (kimi-datasource) | P2 | Auto-pull segment revenue, gross margin trend, operating cash flow vs net income, institutional holder changes, sector peer rally check. Currently manual in pitfall 24 bonus checks. | Medium |
| Korean KOSPI 200 index option template | P2 | Since individual Korean stocks lack LEAPS, add analysis template for KOSPI 200 index options as the Korea proxy vehicle. | Medium |
| Remaining pitfalls audit | P2 | Audit pitfalls 01–20, 22–23 for hard Funda dependencies. Add conditional 🟡 paths where needed. | Medium |
| Case study: PENG or SK Hynix | P3 | Add `references/ticker/peng-2026-05.md` or `skhynix-2026-05.md` demonstrating full 🟡 estimated-data workflow end-to-end. | Low |
| Cleanup: Claude refs, version tags | P3 | Remove any remaining hard-coded Claude/Claude Code references. Add version tag to SKILL.md. | Low |

---

## Phase 4: "Beyond the Bridge" 🔮 FUTURE

**Goal:** Close the gap between estimated and live data.

| Item | Priority | Why | Complexity |
|------|----------|-----|------------|
| IV surface proxy from realized vol term structure | P2 | Use 20D/60D/1Y realized vol to infer IV skew/shape. Better than flat IV assumption in BSM. | High |
| Options flow proxy from social/KOL sentiment | P3 | When volume anomaly is ambiguous, use Reddit/Twitter/KOL mention velocity as demand-IV proxy. Fragile but better than nothing. | High |
| Auto-refresh case studies | P3 | Scheduled re-analysis of open case studies with latest data. | Medium |

---

## How to Use This Roadmap

1. **Pick a phase.** Each phase is designed to fit in one session.
2. **Pick the highest-priority item within the phase.** Don't skip P0.
3. **Validate on a real ticker before marking done.** PENG, NVDA, or 000660.KS are the canonical test cases.
4. **Update this file** when scope changes or items ship.
