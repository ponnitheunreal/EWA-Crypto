import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime

from src.indicator import CryptoElliotWaveIndicator

def quick_test():
    # Minimal synthetic data
    dates = pd.date_range("2025-01-01", periods=100, freq="4h")
    np.random.seed(42)
    close = pd.Series(50000 + np.random.randn(100).cumsum() * 100, index=dates)
    high = close * (1 + np.random.uniform(0, 0.01, 100))
    low = close * (1 - np.random.uniform(0, 0.01, 100))
    open_ = close.shift(1).fillna(close.iloc[0])

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.uniform(100, 1000, 100)
    }, index=dates)

    print("DataFrame created successfully")
    print(f"Close range: {df['close'].min():.2f} - {df['close'].max():.2f}")

    indicator = CryptoElliotWaveIndicator()
    result = indicator.analyze(df)

    print(f"\nWaves detected: {len(result['waves'])}")
    print(f"Signals: {len(result['signals'])}")

    sig = indicator.get_latest_signal(df)
    if sig:
        print(f"Latest: {sig}")
    else:
        print("No signal")

if __name__ == "__main__":
    quick_test()
