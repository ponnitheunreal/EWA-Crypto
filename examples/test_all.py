"""Test all core components quickly."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np

from src import EMA, FibonacciLevels, ElliotWaveDetector, CryptoElliotWaveIndicator

# Generate simple data
np.random.seed(42)
dates = pd.date_range("2025-01-01", periods=100, freq="4h")
close = pd.Series(50000 + np.random.randn(100).cumsum() * 100, index=dates)
high = close * (1 + np.random.uniform(0, 0.01, 100))
low = close * (1 - np.random.uniform(0, 0.01, 100))
df = pd.DataFrame({"open": close.shift(1).fillna(close.iloc[0]), "high": high, "low": low, "close": close})

# Test EMA
ema = EMA(period=21)
ema_vals = ema.calculate(df["close"])
trend = ema.trend_direction(df["close"], ema_vals)
print(f"EMA trend (latest): {trend.iloc[-1]}")

# Test Fib
fib = FibonacciLevels()
rets = fib.calculate_retracements(swing_high=50000, swing_low=45000, direction="bullish")
print(f"Retracement levels: {list(rets.keys())}")

# Test Wave Detector
detector = ElliotWaveDetector()
result = detector.detect(df)
print(f"Waves detected: {len(result['waves'])}")

# Test full indicator
indicator = CryptoElliotWaveIndicator()
results = indicator.analyze(df)
print(f"Signals: {len(results['signals'])}")

print("All components verified successfully.")
