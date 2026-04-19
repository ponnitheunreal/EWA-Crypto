# sample_usage.py - Example Usage of the Crypto Elliot Wave Indicator

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.indicator import CryptoElliotWaveIndicator

# ----------------------------------------------------
# 1. Generate synthetic OHLCV data for demonstration
# ----------------------------------------------------
def generate_synthetic_data(
    periods: int = 500,
    start_price: float = 50000.0,
    trend_strength: float = 0.001,
    volatility: float = 0.02
) -> pd.DataFrame:
    """
    Create synthetic price data exhibiting wave-like behavior.

    Args:
        periods: Number of 4H candles.
        start_price: Initial BTC price.
        trend_strength: Base drift per period.
        volatility: Random walk volatility.

    Returns:
        DataFrame with OHLCV columns.
    """
    dates = pd.date_range(
        start=datetime(2025, 1, 1),
        periods=periods,
        freq="4h"
    )

    prices = [start_price]
    for i in range(1, periods):
        # Add cyclical wave-like movement with mean-reverting component
        cycle = 0.02 * np.sin(i / 30)   # 2% cyclic component
        drift = trend_strength          # small upward drift
        shock = np.random.normal(0, volatility)
        new_price = prices[-1] * (1 + drift + cycle + shock)
        # Prevent negative or zero prices
        if new_price < 1:
            new_price = 1.0
        prices.append(new_price)

    close = pd.Series(prices, index=dates)
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


# ----------------------------------------------------
# 2. Run the indicator
# ----------------------------------------------------
def main():
    print("=" * 60)
    print("Crypto Elliot Wave Indicator — Example Usage")
    print("=" * 60)

    # Generate sample data
    print("\n[1] Generating synthetic 4H OHLCV data ...")
    df = generate_synthetic_data(periods=300, start_price=45000)
    print(f"    Shape: {df.shape}")
    print(f"    Date range: {df.index[0]} -> {df.index[-1]}")
    print(f"    Price range: ${df['low'].min():.0f} - ${df['high'].max():.0f}")

    # Initialize indicator
    print("\n[2] Initializing CryptoElliotWaveIndicator ...")
    indicator = CryptoElliotWaveIndicator(
        ema_period=21,
        swing_window=5,
        min_confidence=0.6
    )

    # Full analysis
    print("\n[3] Running full analysis ...")
    results = indicator.analyze(df)

    # Print wave summary
    waves = results["waves"]
    print(f"\n    Detected {len(waves)} wave segments total")
    impulse_waves = [w for w in waves if indicator.wave_detector.is_impulse_wave(w)]
    print(f"    Impulse waves (1,3,5): {len(impulse_waves)}")
    corrective_waves = [w for w in waves if indicator.wave_detector.is_corrective_wave(w)]
    print(f"    Corrective waves (2,4): {len(corrective_waves)}")

    if waves:
        print("\n    Last 5 waves:")
        for w in waves[-5:]:
            direction_symbol = "^" if w.direction == "up" else "v"
            print(f"      Wave {w.wave_num}{direction_symbol}  "
                  f"{w.start_price:>12.2f} -> {w.end_price:>12.2f}  "
                  f"(conf={w.confidence:.2f})")

    # Print latest Fibonacci levels
    retracements = results.get("retracements", {})
    if retracements:
        print("\n[4] Latest Fibonacci Retracement Levels:")
        print(f"    {'Level':<8} {'Price':>15}")
        print(f"    {'-'*25}")
        for name, price in sorted(retracements.items(), key=lambda x: float(x[1]), reverse=True):
            print(f"    {name:<8} {price:>15.2f}")

    extensions = results.get("extensions", {})
    if extensions:
        print("\n[5] Latest Fibonacci Extension Targets:")
        print(f"    {'Level':<8} {'Target':>15}")
        print(f"    {'-'*25}")
        for name, price in sorted(extensions.items(), key=lambda x: float(x[1])):
            print(f"    {name:<8} {price:>15.2f}")

    # Generate all signals
    print("\n[6] Generating signals ...")
    signal_df = indicator.signal_generator.batch_generate(df)

    if not signal_df.empty:
        print(f"    Total signals generated: {len(signal_df)}")
        print("\n    Recent signals:")
        print(f"    {'Timestamp':<20} {'Type':<6} {'Price':>12} {'Conf':>6} {'Wave':>5} {'Fib Level':<10}")
        print(f"    {'-'*75}")
        for idx, row in signal_df.tail(5).iterrows():
            print(f"    {str(idx):<20} {row['signal']:<6} {row['price']:>12.2f} "
                  f"{row['confidence']:>6.2f} {int(row['wave']):>5} {str(row['fib_level']):<10}")
    else:
        print("    No signals generated (may need more data or different parameters)")

    # Demonstrate single-bar latest signal
    print("\n[7] Latest signal (via get_latest_signal):")
    latest_signal = indicator.get_latest_signal(df)
    if latest_signal:
        print(f"    {latest_signal}")
        print(f"    Stop Loss:     {latest_signal.stop_loss:.2f}")
        tp = latest_signal.take_profit
        if tp is not None:
            print(f"    Take Profit:   {tp:.2f}")
        else:
            print("    Take Profit:   (not set)")
    else:
        print("    No current signal")

    # Support / Resistance
    print("\n[8] Current Support / Resistance:")
    levels = indicator.get_support_resistance(df, lookback=60)
    print(f"    Support:       {[f'${p:,.0f}' for p in levels['support']]}")
    print(f"    Resistance:    {[f'${p:,.0f}' for p in levels['resistance']]}")

    print("\n" + "=" * 60)
    print("Example complete. Modify parameters or data for your use case.")
    print("=" * 60)


if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)
    main()
