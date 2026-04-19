# examples/generate_chart.py
# Professional high-resolution chart generator with multiple format support

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from datetime import datetime

from src.indicator import CryptoElliotWaveIndicator
from src.exchange import fetch_ohlcv
from src.plotting import HighResolutionPlotter, generate_chart


def main():
    print("=" * 70)
    print("High-Resolution Elliot Wave Chart Generator")
    print("=" * 70)
    print("\nSupported formats: PNG (300+ DPI), PDF, SVG (vector)")

    # Configuration — multiple timeframes (HTF first for bias)
    configs = [
        {"symbol": "BTC/USDT", "timeframe": "1d", "limit": 500, "theme": "dark", "dpi": 300},   # HTF
        {"symbol": "BTC/USDT", "timeframe": "4h", "limit": 200, "theme": "light", "dpi": 300},  # LTF
    ]

    htf_data = None  # Store higher timeframe DataFrame for bias

    for cfg in configs:
        symbol = cfg["symbol"]
        timeframe = cfg["timeframe"]
        limit = cfg["limit"]
        theme = cfg.get("theme", "light")
        dpi = cfg.get("dpi", 300)

        print(f"\n{'='*70}")
        print(f"Processing: {symbol} | {timeframe} | theme={theme} | {dpi} DPI")
        print(f"{'='*70}")

        # 1. Fetch data
        print(f"\n[1] Fetching OHLCV from Binance...")
        try:
            df = fetch_ohlcv("binance", symbol, timeframe, limit)
            print(f"    [+] Received {len(df)} candles")
            print(f"    [+]: {df.index[0].strftime('%Y-%m-%d')} -> {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"    [+]: Last price ${df['close'].iloc[-1]:,.2f}")
        except Exception as e:
            print(f"    [!] Network error: {e}")
            df = generate_synthetic_data(limit, timeframe)
            print(f"    [+] Generated {len(df)} synthetic bars (offline mode)")

        # Track higher timeframe data for bias (1d, 1w, etc.)
        is_htf = timeframe in ["1d", "D", "1w", "W"]
        if is_htf:
            htf_data = df  # store for bias comparison
            bias_signal = None
        else:
            # Use HTF bias for lower timeframes
            bias_signal = htf_data

        # 2. Analyze
        print(f"\n[2] Running Elliot Wave analysis...")
        indicator = CryptoElliotWaveIndicator(ema_period=21, swing_window=5, min_confidence=0.6)
        results = indicator.analyze(df)
        latest_signal = indicator.get_latest_signal(df, higher_tf_df=bias_signal)

        waves = results["waves"]
        impulse = sum(1 for w in waves if indicator.wave_detector.is_impulse_wave(w))
        corrective = len(waves) - impulse
        print(f"    Waves: {len(waves)} total | {impulse} impulse | {corrective} corrective")

        if latest_signal:
            print(f"\n[3] Signal detected:")
            print(f"    Type:           {latest_signal.signal_type}")
            print(f"    Signal Type:    {latest_signal.signal_category}")
            print(f"    Trend Context:  {latest_signal.trend_context}")
            print(f"    Entry:          ${latest_signal.price:,.2f}")
            if latest_signal.stop_loss:
                print(f"    Stop Loss:      ${latest_signal.stop_loss:,.2f}")
            if latest_signal.take_profit:
                print(f"    Take Profit:    ${latest_signal.take_profit:,.2f}")
            print(f"    Confidence:     {latest_signal.confidence:.0%}")
            print(f"    Wave:           {latest_signal.wave_num} | Fib: {latest_signal.fib_level}")
        else:
            print(f"\n[3] No signal — conditions not met")

        # 3. Generate charts
        print(f"\n[4] Rendering high-resolution charts...")
        base_name = f"{symbol.replace('/', '_')}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M')}"

        # Multiple format support
        formats_to_save = [
            ("png", dpi),  # High-res raster
            # Uncomment for vector exports:
            # ("pdf", None),  # Vector PDF
            # ("svg", None),  # Vector SVG
        ]

        for fmt, fmt_dpi in formats_to_save:
            filename = f"{base_name}.{fmt}"
            output_path = os.path.join("charts", filename)

            try:
                saved_path = generate_chart(
                    df=df,
                    indicator=indicator,
                    output_path=output_path,
                    symbol=symbol,
                    timeframe=timeframe,
                    theme=theme,
                    dpi=fmt_dpi or dpi,
                    format=fmt  # type: ignore
                )
                size_kb = os.path.getsize(saved_path) / 1024
                print(f"    [+] {fmt.upper()}: {os.path.basename(saved_path)} — {size_kb:.0f} KB")
            except Exception as exc:
                print(f"    [!] Error saving {fmt}: {exc}")

    print("\n" + "=" * 70)
    print("Done. Charts are in the 'charts/' directory.")
    print("=" * 70)


def generate_synthetic_data(periods: int, timeframe: str = "4h") -> pd.DataFrame:
    """Offline test data (used when exchange unavailable)."""
    import numpy as np
    np.random.seed(42)
    freq = "1d" if timeframe == "1d" else "4h"
    dates = pd.date_range("2025-01-01", periods=periods, freq=freq)
    close = pd.Series(50000 + np.random.randn(periods).cumsum() * 200, index=dates)
    high = close * (1 + np.random.uniform(0, 0.008, periods))
    low = close * (1 - np.random.uniform(0, 0.008, periods))
    open_ = close.shift(1).fillna(close.iloc[0])
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close,
        "volume": np.random.uniform(500, 5000, periods)
    }, index=dates)


if __name__ == "__main__":
    main()
