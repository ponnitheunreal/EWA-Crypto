# examples/generate_chart.py
# Professional chart generator: fetch data → analyze → save detailed annotated chart

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime

from src.indicator import CryptoElliotWaveIndicator
from src.exchange import fetch_ohlcv
from src.plotting import generate_chart


def main():
    print("=" * 70)
    print("Professional Elliot Wave Chart Generator")
    print("=" * 70)

    # Configuration - supports any timeframe
    configs = [
        {"symbol": "BTC/USDT", "timeframe": "4h", "limit": 300},
        {"symbol": "BTC/USDT", "timeframe": "1d", "limit": 200},  # Daily
    ]

    for cfg in configs:
        symbol = cfg["symbol"]
        timeframe = cfg["timeframe"]
        limit = cfg["limit"]

        print(f"\n{'='*70}")
        print(f"Processing: {symbol} | Timeframe: {timeframe} | Bars: {limit}")
        print(f"{'='*70}")

        # 1. Fetch data
        print(f"\n[1] Fetching OHLCV from Binance...")
        try:
            df = fetch_ohlcv("binance", symbol, timeframe, limit)
            print(f"    [+] Received {len(df)} candles")
            print(f"    Range: {df.index[0].strftime('%Y-%m-%d')} -> {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"    Price: ${df['close'].iloc[-1]:,.2f}")
        except Exception as e:
            print(f"    [!] Fetch error: {e}")
            df = generate_synthetic_data(limit, timeframe)
            print(f"    [+] Generated {len(df)} synthetic bars")

        # 2. Analyze
        print(f"\n[2] Running Elliot Wave analysis...")
        indicator = CryptoElliotWaveIndicator(
            ema_period=21,
            swing_window=5,
            min_confidence=0.6
        )
        results = indicator.analyze(df)
        waves = results["waves"]
        signals_df = results["signals"]
        latest_signal = indicator.get_latest_signal(df)

        print(f"    Waves detected: {len(waves)}")
        impulse = sum(1 for w in waves if indicator.wave_detector.is_impulse_wave(w))
        print(f"    Impulse (1,3,5): {impulse} | Corrective (2,4): {len(waves)-impulse}")

        if latest_signal:
            print(f"\n[3] Latest Signal:")
            print(f"    Type:       {latest_signal.signal_type}")
            print(f"    Entry:      ${latest_signal.price:,.2f}")
            if latest_signal.stop_loss:
                print(f"    Stop Loss:  ${latest_signal.stop_loss:,.2f}")
            if latest_signal.take_profit:
                print(f"    Take Profit:${latest_signal.take_profit:,.2f}")
            print(f"    Confidence: {latest_signal.confidence:.0%}")
            print(f"    Wave:       {latest_signal.wave_num}")
            print(f"    Fib Level:  {latest_signal.fib_level}")
        else:
            print(f"\n[3] No signal on current chart")

        # 3. Generate chart
        print(f"\n[4] Generating professional chart...")

        # Build filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        symbol_clean = symbol.replace("/", "_")
        filename = f"{symbol_clean}_{timeframe}_{timestamp}.png"
        output_path = os.path.join("charts", filename)

        try:
            saved = generate_chart(
                df=df,
                indicator=indicator,
                output_path=output_path,
                symbol=symbol,
                timeframe=timeframe,
                dpi=200,
                show_plot=False
            )
            size_mb = os.path.getsize(saved) / 1024
            print(f"    [OK] Chart saved: {saved}")
            print(f"    Size: {size_mb:.1f} KB | 200 DPI | Multi-panel (price+volume)")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            import traceback; traceback.print_exc()

    print("\n" + "=" * 70)
    print("All charts generated. Check the 'charts/' folder.")
    print("=" * 70)


def generate_synthetic_data(periods: int, timeframe: str = "4h") -> pd.DataFrame:
    """Generate synthetic OHLCV for testing."""
    np.random.seed(42)

    if timeframe == "1d":
        freq = "1d"
    elif timeframe == "4h":
        freq = "4h"
    else:
        freq = "1h"

    dates = pd.date_range("2025-01-01", periods=periods, freq=freq)
    close = pd.Series(50000 + np.random.randn(periods).cumsum() * 200, index=dates)
    high = close * (1 + np.random.uniform(0, 0.008, periods))
    low = close * (1 - np.random.uniform(0, 0.008, periods))
    open_ = close.shift(1).fillna(close.iloc[0])

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.uniform(500, 5000, periods)
    }, index=dates)
    return df


if __name__ == "__main__":
    main()
