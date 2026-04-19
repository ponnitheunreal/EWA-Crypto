import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd
import numpy as np
from src.indicator import CryptoElliotWaveIndicator
from src.exchange import fetch_ohlcv
from src.plotting import generate_chart

np.random.seed(42)
dates = pd.date_range("2025-01-01", periods=100, freq="4h")
close = pd.Series(50000 + np.random.randn(100).cumsum() * 100, index=dates)
high = close * (1 + np.random.uniform(0, 0.01, 100))
low = close * (1 - np.random.uniform(0, 0.01, 100))
df = pd.DataFrame({"open": close.shift(1).fillna(close.iloc[0]), "high": high, "low": low, "close": close, "volume": np.random.uniform(100,1000,100)}, index=dates)

indicator = CryptoElliotWaveIndicator()
try:
    path = generate_chart(df, indicator, "charts/test.png", symbol="BTC/USDT", timeframe="4h", theme="light", dpi=300, format="png")
    print("SUCCESS:", path)
except Exception as e:
    import traceback; traceback.print_exc()
