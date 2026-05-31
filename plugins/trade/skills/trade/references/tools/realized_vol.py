#!/usr/bin/env python3
"""
Realized Volatility Calculator for Trade Skill + kimi-datasource

Usage:
    python3 realized_vol.py --input /tmp/PENG_history.csv
    python3 realized_vol.py --input /tmp/PENG_history.csv --output /tmp/PENG_vol.json
    python3 realized_vol.py --input /tmp/SK_hynix_yf_history.csv --currency KRW

Input: CSV from stock_finance_data_get_price or yahoo_finance with columns including 'close'
Output: Realized vol metrics and IV Rank proxy
"""

import argparse
import json
import sys

import numpy as np
import pandas as pd


def compute_realized_vol(returns: pd.Series, window: int) -> float:
    """Annualized realized volatility from daily returns."""
    if len(returns) < window:
        return np.nan
    return returns.tail(window).std() * np.sqrt(252)


def compute_iv_rank_proxy(rolling_vol: pd.Series, current_vol: float) -> float:
    """Percentile of current vol within 1-year rolling history."""
    valid = rolling_vol.dropna()
    if len(valid) == 0:
        return np.nan
    return (valid < current_vol).mean() * 100


def analyze(input_path: str, output_path: str | None = None, currency_override: str | None = None) -> dict:
    df = pd.read_csv(input_path)

    # Normalize column names (kimi-datasource uses 'close' or 'Close')
    df.columns = [c.lower().strip() for c in df.columns]

    if "close" not in df.columns:
        raise ValueError(f"CSV must contain a 'close' column. Found: {list(df.columns)}")

    # Detect currency: CLI override > CSV column > default USD
    currency = currency_override
    if currency is None and "currency" in df.columns:
        currency = str(df["currency"].iloc[0]).strip().upper()
    currency = currency or "USD"

    # Ensure chronological order
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time").reset_index(drop=True)

    df["returns"] = df["close"].pct_change()

    # Core realized vol metrics
    rv_20d = compute_realized_vol(df["returns"], 20)
    rv_60d = compute_realized_vol(df["returns"], 60)
    rv_1y = compute_realized_vol(df["returns"], 252)

    # Rolling 20-day realized vol for IV Rank proxy
    df["rv_20d_roll"] = df["returns"].rolling(window=20).std() * np.sqrt(252)

    # IV Rank proxy: percentile of current 20d vol in 1-year rolling history
    # Use 252 trading days ≈ 1 year
    iv_rank_proxy = compute_iv_rank_proxy(df["rv_20d_roll"], rv_20d)

    # IV Percentile proxy: same metric, labeled clearly
    iv_percentile_proxy = iv_rank_proxy

    # Price context
    current_price = df["close"].iloc[-1]
    price_1y_ago = df["close"].iloc[-min(252, len(df))]
    price_20d_ago = df["close"].iloc[-min(20, len(df))]
    price_60d_ago = df["close"].iloc[-min(60, len(df))]

    # Recent returns
    ret_20d = (current_price / price_20d_ago - 1) * 100
    ret_60d = (current_price / price_60d_ago - 1) * 100
    ret_1y = (current_price / price_1y_ago - 1) * 100

    # 52-week (or max available) high/low
    lookback = min(252, len(df))
    high_1y = df["high"].tail(lookback).max() if "high" in df.columns else np.nan
    low_1y = df["low"].tail(lookback).min() if "low" in df.columns else np.nan

    result = {
        "input_file": input_path,
        "currency": currency,
        "price": {
            "current": round(float(current_price), 2),
            "high_1y": round(float(high_1y), 2) if not pd.isna(high_1y) else None,
            "low_1y": round(float(low_1y), 2) if not pd.isna(low_1y) else None,
            "ret_20d_pct": round(float(ret_20d), 1),
            "ret_60d_pct": round(float(ret_60d), 1),
            "ret_1y_pct": round(float(ret_1y), 1),
        },
        "realized_volatility": {
            "rv_20d_annualized": round(float(rv_20d) * 100, 2),
            "rv_60d_annualized": round(float(rv_60d) * 100, 2),
            "rv_1y_annualized": round(float(rv_1y) * 100, 2),
        },
        "iv_proxy": {
            "estimated_iv": round(float(rv_60d + 0.05) * 100, 2),
            "method": "realized_vol_60d + 5pp",
            "confidence": "low_to_medium",
        },
        "iv_rank_proxy": {
            "value": round(float(iv_rank_proxy), 1) if not pd.isna(iv_rank_proxy) else None,
            "method": "current_20d_rv_percentile_in_1y_rolling_history",
            "confidence": "medium",
        },
        "regime_indicators": {
            "high_vol": bool(rv_20d > 0.50),
            "extreme_vol": bool(rv_20d > 0.80),
            "parabolic_20d": bool(ret_20d > 30),
            "parabolic_60d": bool(ret_60d > 50),
        },
    }

    return result


def print_results(result: dict) -> None:
    currency = result.get("currency", "USD")
    print("=" * 60)
    print("REALIZED VOLATILITY ANALYSIS")
    print("=" * 60)
    print()
    p = result["price"]
    print(f"Current Price:        {currency} {p['current']:,.2f}")
    if p["high_1y"] is not None:
        print(f"1Y High:              {currency} {p['high_1y']:,.2f}")
    if p["low_1y"] is not None:
        print(f"1Y Low:               {currency} {p['low_1y']:,.2f}")
    print(f"20D Return:           {p['ret_20d_pct']:+.1f}%")
    print(f"60D Return:           {p['ret_60d_pct']:+.1f}%")
    print(f"1Y Return:            {p['ret_1y_pct']:+.1f}%")
    print()

    rv = result["realized_volatility"]
    print("REALIZED VOLATILITY:")
    print(f"  20D Annualized:     {rv['rv_20d_annualized']:.1f}%")
    print(f"  60D Annualized:     {rv['rv_60d_annualized']:.1f}%")
    print(f"  1Y Annualized:      {rv['rv_1y_annualized']:.1f}%")
    print()

    iv = result["iv_proxy"]
    print("IV PROXY (Estimated):")
    print(f"  Estimated IV:       {iv['estimated_iv']:.1f}%")
    print(f"  Method:             {iv['method']}")
    print(f"  Confidence:         {iv['confidence']}")
    print()

    rank = result["iv_rank_proxy"]
    if rank["value"] is not None:
        print("IV RANK PROXY:")
        print(f"  Value:              {rank['value']:.1f}")
        print(f"  Method:             {rank['method']}")
        print(f"  Confidence:         {rank['confidence']}")
        print()

    reg = result["regime_indicators"]
    print("REGIME FLAGS:")
    print(f"  High Vol (>50%):    {reg['high_vol']}")
    print(f"  Extreme Vol (>80%): {reg['extreme_vol']}")
    print(f"  Parabolic 20D:      {reg['parabolic_20d']}")
    print(f"  Parabolic 60D:      {reg['parabolic_60d']}")
    print()

    print("=" * 60)
    print("HONESTY REQUIREMENT:")
    print("  IV estimated from realized volatility. Actual market IV may")
    print("  differ +/-15-30 percentage points. Greeks and breakevens")
    print("  are approximate.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Compute realized volatility and IV proxy from price history CSV"
    )
    parser.add_argument("--input", "-i", required=True, help="Path to price history CSV")
    parser.add_argument("--output", "-o", help="Optional path to write JSON output")
    parser.add_argument("--currency", "-c", help="Currency code override (e.g., KRW, USD). Auto-detected from CSV if available.")
    args = parser.parse_args()

    try:
        result = analyze(args.input, args.output, currency_override=args.currency)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print_results(result)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nJSON output written to: {args.output}")


if __name__ == "__main__":
    main()
