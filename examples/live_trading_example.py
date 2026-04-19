# examples/live_trading_example.py
# Demonstrates fetching live OHLCV data from an exchange using CCXT
# and running the Elliot Wave indicator on it.

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime

from src.indicator import CryptoElliotWaveIndicator
from src.exchange import ExchangeFetcher, fetch_ohlcv


def main():
    print("=" * 60)
    print("Live Exchange Data Example — Crypto Elliot Wave Indicator")
    print("=" * 60)

    # Configuration — analyze both LTF (4H) and HTF (1D) with bias
    configs = [
        {"timeframe": "1d", "limit": 500, "label": "Daily (HTF Bias)"},
        {"timeframe": "4h", "limit": 200, "label": "4-Hour (LTF)"},
    ]

    exchange_id = "binance"
    symbol = "BTC/USDT"
    htf_df = None  # Store higher timeframe data for bias

    for cfg in configs:
        timeframe = cfg["timeframe"]
        limit = cfg["limit"]
        label = cfg["label"]

        print(f"\n{'='*60}")
        print(f"[{label}] {symbol} | {timeframe} | {limit} candles")
        print(f"{'='*60}")

        print(f"\n[1] Fetching OHLCV data from {exchange_id.upper()}...")
        try:
            fetcher = ExchangeFetcher(exchange_id)
            df = fetcher.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
            print(f"    Fetched {len(df)} candles")
            print(f"    Date range: {df.index[0]} -> {df.index[-1]}")
            print(f"    Latest close: ${df['close'].iloc[-1]:,.2f}")
        except Exception as e:
            print(f"    ERROR: {e}")
            print("    Using synthetic fallback data...")
            df = generate_fallback_data(limit, timeframe)
            print(f"    Generated {len(df)} synthetic bars")

        # Track HTF for bias (1d = higher timeframe)
        if timeframe in ["1d", "D", "1w", "W"]:
            htf_df = df

        # Initialize and analyze
        print("\n[2] Initializing CryptoElliotWaveIndicator...")
        indicator = CryptoElliotWaveIndicator(ema_period=21, swing_window=5, min_confidence=0.6)

        print("\n[3] Running analysis...")
        results = indicator.analyze(df)
        waves = results["waves"]
        print(f"    Waves detected: {len(waves)}")
        if waves:
            impulse_count = sum(1 for w in waves if indicator.wave_detector.is_impulse_wave(w))
            print(f"    Impulse waves (1,3,5): {impulse_count}")
            print(f"    Corrective waves (2,4): {len(waves) - impulse_count}")

        # Fibonacci levels
        retracements = results.get("retracements", {})
        if retracements:
            print("\n[4] Fibonacci Retracement Zones (latest):")
            print(f"    {'Level':<8} {'Price':>15}")
            print(f"    {'-'*25}")
            for name, price in sorted(retracements.items(), key=lambda x: float(x[1]), reverse=True):
                print(f"    {name:<8} {price:>15,.2f}")

            extensions = results.get("extensions", {})
            if extensions:
                print("\n[5] Fibonacci Extension Targets:")
                print(f"    {'Level':<8} {'Target':>15}")
                print(f"    {'-'*25}")
                for name, price in sorted(extensions.items(), key=lambda x: float(x[1])):
                    print(f"    {name:<8} {price:>15,.2f}")

        # Signals
        print("\n[6] Signal Scan:")
        signal_df = results["signals"]
        if not signal_df.empty:
            print(f"    Total signals in history: {len(signal_df)}")
            print("\n    Latest signals:")
            print(f"    {'Timestamp':<20} {'Type':<6} {'Price':>12} {'Conf':>6} {'Wave':>5} {'Fib Level':<10}")
            print(f"    {'-'*75}")
            for idx, row in signal_df.tail(5).iterrows():
                print(f"    {str(idx):<20} {row['signal']:<6} {row['price']:>12,.2f} "
                      f"{row['confidence']:>6.2f} {int(row['wave']):>5} {str(row['fib_level']):<10}")
        else:
            print("    No signals detected in current dataset")

        # Latest signal with HTF bias (if available)
        print("\n[7] Latest Signal:")
        latest_signal = indicator.get_latest_signal(df, higher_tf_df=htf_df if timeframe not in ["1d", "D", "1w", "W"] else None)
        if latest_signal:
            print(f"    {latest_signal}")
            print(f"    Stop Loss:     {latest_signal.stop_loss:,.2f}")
            if latest_signal.take_profit:
                print(f"    Take Profit:   {latest_signal.take_profit:,.2f}")
            else:
                print("    Take Profit:   (not set — price may not be near extension)")
            # Additional context
            print(f"    Signal Type:   {latest_signal.signal_category}")
            print(f"    Trend Context: {latest_signal.trend_context}")
        else:
            print("    No signal — conditions not met")

        # Support / Resistance
        print("\n[8] Current S/R Levels:")
        levels = indicator.get_support_resistance(df, lookback=60)
        print(f"    Support:    {[f'${p:,.0f}' for p in levels['support']]}")
        print(f"    Resistance: {[f'${p:,.0f}' for p in levels['resistance']]}")

    print("\n" + "=" * 60)
    print("Done. Adjust parameters or timeframe as needed.")
    print("=" * 60)


def generate_fallback_data(periods: int = 500, timeframe: str = "4h") -> pd.DataFrame:
    """Generate synthetic data if exchange fetch fails (for testing offline)."""
    np.random.seed(42)
    freq = "1d" if timeframe == "1d" else "4h"
    dates = pd.date_range("2025-01-01", periods=periods, freq=freq)
    close = pd.Series(50000 + np.random.randn(periods).cumsum() * 100, index=dates)
    high = close * (1 + np.random.uniform(0, 0.01, periods))
    low = close * (1 - np.random.uniform(0, 0.01, periods))
    open_ = close.shift(1).fillna(close.iloc[0])

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.uniform(100, 1000, periods)
    }, index=dates)
    return df


if __name__ == "__main__":
    main()
