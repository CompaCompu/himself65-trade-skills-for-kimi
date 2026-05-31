#!/usr/bin/env python3
"""
Black-Scholes-Merton Option Pricer for Trade Skill + kimi-datasource

Estimates option premiums, Greeks, and extrinsic percentages when live
options chains are unavailable.

Usage:
    python3 bsm_quick.py --stock 55.83 --strikes 25,30,60,70,85 --iv 1.057 --days 240
    python3 bsm_quick.py --stock 2333000 --strikes 1000000,1500000 --iv 0.978 --days 180 --currency KRW

Output: Formatted table with premium, delta, gamma, theta, vega, extrinsic%, breakeven
"""

import argparse
import json
import sys
from math import exp, log, pi, sqrt

import numpy as np
from scipy.stats import norm


def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> dict:
    """
    Compute Black-Scholes call price and Greeks.
    """
    if sigma <= 0 or T <= 0:
        intrinsic = max(S - K, 0)
        return {
            "price": intrinsic,
            "delta": 1.0 if S > K else 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
            "intrinsic": intrinsic,
            "extrinsic": 0.0,
            "extrinsic_pct": 0.0,
            "breakeven": K,
        }

    d1 = (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    nd1 = norm.cdf(d1)
    nd2 = norm.cdf(d2)
    n_prime_d1 = norm.pdf(d1)

    price = S * exp(-q * T) * nd1 - K * exp(-r * T) * nd2

    delta = exp(-q * T) * nd1
    gamma = exp(-q * T) * n_prime_d1 / (S * sigma * sqrt(T))
    theta = (-S * exp(-q * T) * n_prime_d1 * sigma / (2.0 * sqrt(T))
             - r * K * exp(-r * T) * nd2
             + q * S * exp(-q * T) * nd1)
    vega = S * exp(-q * T) * n_prime_d1 * sqrt(T) * 0.01
    rho = K * T * exp(-r * T) * nd2 * 0.01

    intrinsic = max(S - K, 0.0)
    extrinsic = price - intrinsic
    extrinsic_pct = (extrinsic / price * 100.0) if price > 0 else 0.0
    breakeven = K + price

    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho,
        "intrinsic": intrinsic,
        "extrinsic": extrinsic,
        "extrinsic_pct": extrinsic_pct,
        "breakeven": breakeven,
        "d1": d1,
        "d2": d2,
    }


def _fmt_money(value: float, currency: str, decimals: int = 2) -> str:
    """Format a monetary value with currency code and commas."""
    return f"{currency} {value:,.{decimals}f}"


def _fmt_gamma(gamma: float) -> str:
    """Adaptive gamma formatting: scientific notation for very small values."""
    if gamma < 0.0001:
        return f"{gamma:.2e}"
    return f"{gamma:>10.5f}"


def print_table(results: list[dict], S: float, sigma: float, T: float, currency: str) -> None:
    width = 110 if S > 10000 else 100
    print("=" * width)
    print(f"BLACK-SCHOLES-MERTON CALL ANALYSIS")
    print(f"Spot: {_fmt_money(S, currency)}  |  IV: {sigma*100:.2f}%  |  Days: {T*365:.0f}  |  Time: {T:.4f}y")
    print("=" * width)
    print()

    header = (
        f"{'Strike':>14}  {'Premium':>14}  {'Delta':>7}  {'Gamma':>12}  "
        f"{'Theta':>14}  {'Vega':>10}  {'Extr%':>7}  {'Breakeven':>14}  {'Status':>12}"
    )
    print(header)
    print("-" * width)

    for r in results:
        status = ""
        if r["extrinsic_pct"] < 10:
            status = "LEAPS_OK"
        elif r["extrinsic_pct"] < 20:
            status = "MARGINAL"
        else:
            status = "SPECULATION"

        line = (
            f"{_fmt_money(r['strike'], currency):>14}  "
            f"{_fmt_money(r['price'], currency):>14}  "
            f"{r['delta']:>7.3f}  "
            f"{_fmt_gamma(r['gamma']):>12}  "
            f"{_fmt_money(r['theta'], currency):>14}  "
            f"{_fmt_money(r['vega'], currency):>10}  "
            f"{r['extrinsic_pct']:>6.1f}%  "
            f"{_fmt_money(r['breakeven'], currency):>14}  "
            f"{status:>12}"
        )
        print(line)

    print()
    print("NOTES:")
    print("  - Premium shown is per share. Multiply by 100 for contract value.")
    print("  - Theta shown is daily decay per share (negative = you lose).")
    print("  - Vega shown is per 1% IV change.")
    print("  - 'LEAPS_OK' = extrinsic < 10% (stock replacement boundary).")
    print("  - 'SPECULATION' = extrinsic > 20% (leveraged bet, not replacement).")
    print()

    if S > 100000:
        print("  - Theta/Vega scale with nominal price. These are absolute values,")
        print("    not percentages. Divide by spot price for %-of-position context.")
        print()

    leaps_ok = [r for r in results if r["extrinsic_pct"] < 10]
    if leaps_ok:
        max_leaps_strike = max(r["strike"] for r in leaps_ok)
        print(f"LEAPS STOCK REPLACEMENT BOUNDARY: <= {_fmt_money(max_leaps_strike, currency, 0)}")
    else:
        print("LEAPS STOCK REPLACEMENT: No strike satisfies extrinsic < 10% at this IV.")

    print()
    print("HONESTY REQUIREMENT:")
    print("  BSM ignores bid-ask spreads, skew, and early exercise. Actual market")
    print("  prices may differ +/-10-20% (more for OTM). Use as directional")
    print("  estimate only, not for final execution pricing.")
    print("=" * width)


def main():
    parser = argparse.ArgumentParser(
        description="BSM call option pricer for trade skill analysis"
    )
    parser.add_argument("--stock", "-s", type=float, required=True, help="Current stock price")
    parser.add_argument("--strikes", "-k", type=str, required=True,
                        help="Comma-separated strike prices (e.g., 25,30,60,70)")
    parser.add_argument("--iv", "-v", type=float, required=True,
                        help="Annualized implied volatility as decimal (e.g., 1.05 for 105%)")
    parser.add_argument("--days", "-d", type=float, required=True,
                        help="Days to expiration")
    parser.add_argument("--rate", "-r", type=float, default=0.045,
                        help="Risk-free rate as decimal (default: 0.045)")
    parser.add_argument("--div", "-q", type=float, default=0.0,
                        help="Dividend yield as decimal (default: 0.0)")
    parser.add_argument("--currency", "-c", type=str, default="USD",
                        help="Currency code for output (default: USD)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        strikes = [float(k.strip()) for k in args.strikes.split(",")]
    except ValueError:
        print("Error: Strikes must be comma-separated numbers.", file=sys.stderr)
        sys.exit(1)

    S = args.stock
    T = args.days / 365.0
    sigma = args.iv
    r = args.rate
    q = args.div
    currency = args.currency.upper()

    if sigma <= 0:
        print("Error: IV must be positive.", file=sys.stderr)
        sys.exit(1)
    if T <= 0:
        print("Error: Days to expiration must be positive.", file=sys.stderr)
        sys.exit(1)

    results = []
    for K in strikes:
        bsm = black_scholes_call(S, K, T, r, sigma, q)
        bsm["strike"] = K
        results.append(bsm)

    if args.json:
        clean_results = []
        for res in results:
            clean = {k: float(v) if isinstance(v, (float, int, np.floating, np.integer)) else v
                     for k, v in res.items()}
            clean_results.append(clean)
        print(json.dumps(clean_results, indent=2))
    else:
        print_table(results, S, sigma, T, currency)


if __name__ == "__main__":
    main()
