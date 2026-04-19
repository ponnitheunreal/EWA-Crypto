"""Quick test of live exchange fetch."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.exchange import fetch_ohlcv

print("Fetching 5 BTC/USDT 4H candles from Binance...")
df = fetch_ohlcv("binance", "BTC/USDT", "4h", limit=5)
print(df[["open", "high", "low", "close", "volume"]])
print(f"\nLatest close: ${df['close'].iloc[-1]:,.2f}")
print("Live fetch successful!")
