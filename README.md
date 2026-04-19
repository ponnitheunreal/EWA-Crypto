# Crypto Elliot Wave Trading Indicator

A Python-based trading indicator that combines **Elliot Wave Theory**, **EMA 21 trend filtering**, and **Fibonacci retracement/extension levels** to generate high-confidence BUY/SELL signals for cryptocurrency (or any asset) on 4H and Daily timeframes.

---

## Features

- **EMA 21** — Trend filter (price above = bullish, below = bearish)
- **Elliot Wave Detection** — Automatic swing point identification and wave labeling (Waves 1–5)
- **Fibonacci Analysis** — Retracement zones and extension targets
- **Signal Generation** — Confluence-based BUY/SELL signals with stop-loss & take-profit
- **Risk Management** — ATR-based stops, confidence scoring

---

## Installation

### 1. Clone or download this repository

```bash
cd H:\Project\Elliot\ wave
```

### 2. Create virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
pandas>=2.0.0
numpy>=1.24.0
```

---

## Quick Start

```python
import pandas as pd
from src import CryptoElliotWaveIndicator

# Load your OHLCV data (CSV with timestamp, open, high, low, close, volume)
df = pd.read_csv("btc_4h.csv", parse_dates=["timestamp"], index_col="timestamp")

# Initialize indicator
indicator = CryptoElliotWaveIndicator(
    ema_period=21,      # EMA period
    swing_window=5,     # Swing detection lookback
    min_confidence=0.6  # Minimum signal confidence
)

# Run full analysis
results = indicator.analyze(df)

# View latest signal
signal = indicator.get_latest_signal(df)
if signal:
    print(signal)
    print(f"Stop Loss: {signal.stop_loss}")
    print(f"Take Profit: {signal.take_profit}")

# Access all generated signals
signals_df = results["signals"]
print(signals_df.tail())
```

---

## Project Structure

```
Elliot wave/
├── src/
│   ├── __init__.py          # Public API exports
│   ├── ema.py               # EMA 21 calculation
│   ├── elliot_wave.py       # Wave detection via swing points
│   ├── fibonacci.py         # Fib retracement & extension
│   ├── signals.py           # Buy/Sell engine
│   ├── indicator.py         # Unified main API
│   ├── exchange.py          # Live data fetcher (CCXT)
│   ├── plotting.py          # Chart generation (matplotlib)
│   └── utils.py             # Helper functions
├── docs/
│   ├── ELLIOT_WAVE_THEORY.md  # Wave detection methodology
│   ├── FIBONACCI_LEVELS.md    # Fib calculation formulas
│   ├── SIGNALS.md             # Signal conditions & scoring
│   └── API.md                 # Complete API reference
├── examples/
│   ├── sample_usage.py          # Full example (synthetic)
│   ├── live_trading_example.py   # Live CCXT integration
│   ├── generate_chart.py         # Chart generator script
│   ├── quick_test.py             # Minimal validation
│   └── test_all.py               # Component smoke test
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── venv/                   # Virtual environment (created locally)
```

---

## Signal Conditions

### BUY Signal

```
1. EMA 21 = BULLISH (close > EMA 21)
2. Elliot Wave = Wave 3 or Wave 5 forming (impulse wave)
3. Price = at Fibonacci support zone (38.2%, 50%, or 61.8% retracement)
4. Confluence = price approaching next Fibonacci extension target
```

### SELL Signal

```
1. EMA 21 = BEARISH (close < EMA 21)
2. Elliot Wave = Wave 3 or Wave 5 forming (downward impulse)
3. Price = at Fibonacci resistance
4. Confluence = price at/approaching bearish extension target
```

### Stop-Loss & Take-Profit

- **Stop-Loss**: 1.5 × ATR(14) below/above entry
- **Take-Profit**: Nearest Fibonacci extension level (FE1=161.8%, FE2=261.8%)

---

## Configuration

```python
# Customize Fibonacci ratios
from src.fibonacci import FibonacciLevels
custom_fib = FibonacciLevels(
    retracement_ratios=[0.382, 0.5, 0.618],  # Simplify to 3 zones
    extension_ratios=[1.618, 2.618, 4.236]
)

# Customize signal sensitivity
indicator = CryptoElliotWaveIndicator(
    ema_period=21,
    swing_window=5,       # Higher = fewer swings, smoother
    min_confidence=0.65   # Higher = fewer but stronger signals
)
```

---

## Supported Data

**Required columns:**
- `open` — Open price
- `high` — High price
- `low` — Low price
- `close` — Close price

**Optional column:**
- `volume` — Trading volume (not currently used)

**Recommended timeframes:**
- 4-Hour (4H)
- Daily (1D)

**Recommended assets:**
- Cryptocurrencies (BTC, ETH, etc.)
- Forex pairs
- Any liquid market with clear swings

---

## Usage Examples

### Generate All Historical Signals

```python
# Returns DataFrame with one row per signal
signals_df = indicator.signal_generator.batch_generate(df)
print(f"Total signals: {len(signals_df)}")
print(signals_df[["signal", "confidence", "wave", "fib_level", "stop_loss", "take_profit"]])
```

### Get Support & Resistance Levels

```python
levels = indicator.get_support_resistance(df, lookback=50)
print("Support:", levels["support"])
print("Resistance:", levels["resistance"])
```

### Inspect Wave Structure

```python
result = indicator.analyze(df)
waves = result["waves"]
for wave in waves[-5:]:  # Last 5 waves
    print(f"Wave {wave.wave_num} {wave.direction}: {wave.start_price:.2f} → {wave.end_price:.2f}")
```

---

## Risk Management Notes

⚠️ **Important:**

- Never trade against the EMA 21 trend direction
- Maximum **2% risk per trade** (position sizing)
- Stop-losses are mandatory — use provided ATR-based stops
- Signals at non-Fib levels or with low confidence (<0.6) should be filtered out

---

## Implementation Details

| Component | Algorithm | Reference |
|-----------|-----------|-----------|
| EMA | Standard exponential smoothing: `EMA_t = (Close_t × k) + (EMA_t-1 × (1-k))` | Wilder's smoothing |
| Swing Detection | Rolling-window local extrema (window=5) | Price-action pivot logic |
| Elliot Wave | Alternating impulse/corrective labeling | Frost & Prechter |
| Fibonacci | Standard ratios from swing extremes | 0.382, 0.5, 0.618, 1.618, 2.618 |

---

## Testing

A sample usage script is provided in `examples/sample_usage.py`:

```bash
python examples/sample_usage.py
```

This demonstrates a full pipeline with synthetic data.

---

## Live Data Integration

The indicator is data-source agnostic. Use `ccxt` to fetch live OHLCV from 100+ exchanges:

### Installation

```bash
pip install ccxt
```

### One-Liner Fetch

```python
from src.exchange import fetch_ohlcv

# Fetch BTC/USDT 4H candles from Binance
df = fetch_ohlcv(
    exchange_id="binance",
    symbol="BTC/USDT",
    timeframe="4h",
    limit=500
)

indicator = CryptoElliotWaveIndicator()
results = indicator.analyze(df)
```

### Full Example with Error Handling

```python
from src.exchange import ExchangeFetcher
from src.indicator import CryptoElliotWaveIndicator

fetcher = ExchangeFetcher("binance")  # or "coinbase", "kraken", "bybit", etc.

try:
    df = fetcher.fetch_ohlcv(
        symbol="BTC/USDT",
        timeframe="4h",
        limit=500
    )
    indicator = CryptoElliotWaveIndicator()
    results = indicator.analyze(df)
    signal = indicator.get_latest_signal(df)
    if signal:
        print(f"Signal: {signal.signal_type} @ ${signal.price:,.2f}")
except Exception as e:
    print(f"Exchange error: {e}")
```

### Current Price Only

```python
from src.exchange import fetch_current_price

price = fetch_current_price("binance", "BTC/USDT")
print(f"Current BTC/USDT: ${price:,.2f}")
```

### Supported Exchanges

All CCXT-supported exchanges: Binance, Coinbase, Kraken, KuCoin, OKX, Bybit, Bitfinex, and 100+ more. See [ccxt.io](https://ccxt.io) for full list.

---

## Chart Generation

Generate annotated PNG charts showing waves, signals, and TP/SL levels:

### One-Liner Chart Save

```python
from src.plotting import generate_chart
from src.indicator import CryptoElliotWaveIndicator
from src.exchange import fetch_ohlcv

# Fetch data
df = fetch_ohlcv("binance", "BTC/USDT", "4h", 200)

# Analyze
indicator = CryptoElliotWaveIndicator()
signal = indicator.get_latest_signal(df)

# Save chart to folder
path = generate_chart(df, indicator, "charts/btc_4h.png")
print(f"Chart saved: {path}")
```

### Full Control (WavePlotter class)

```python
from src.plotting import WavePlotter

plotter = WavePlotter(indicator, style="seaborn-v0_8-darkgrid", figsize=(16, 10))
plotter.plot(
    df=df,
    signals_df=results["signals"],
    latest_signal=signal,
    output_path="charts/my_chart.png",
    dpi=200,
    show_plot=False
)
```

### What's Plotted

- Candlestick price action (high/low shaded, close line)
- EMA 21 overlay
- Detected Elliot Waves (colored lines with wave numbers)
- Fibonacci retracement zones (blue dotted lines)
- Fibonacci extension targets (purple dash-dot lines)
- BUY/SELL markers (green ▲ / red ▼)
- Entry (gold star), Stop-Loss (red dashed), Take-Profit (green dashed)
- Support / resistance levels from recent swings

### Output

Charts save as high-resolution PNG (200 DPI default) to any folder. Directory is created automatically.

```bash
python examples/generate_chart.py
# Creates: charts/BTC_USDT_4h_YYYYMMDD_HHMM.png
```

---

## Limitations & Disclaimers

- **Not financial advice** — For educational purposes only
- **Historical performance ≠ future results** — Always backtest thoroughly
- **Swing detection is heuristic** — May miss complex corrections or multiple wave counts
- **Markets change** — Fib ratios work best in trending, liquid markets
- **No alerts built-in** — Alerts can be added in Phase 4 (bonus)

---

## References

- *Elliott Wave Principle* — Frost & Prechter
- *Fibonacci analysis* — Classic trading ratios
- `pandas` and `numpy` for vectorized numerical computing

---

## License

MIT (or project-specific license)

---

## Support

Report issues at: https://github.com/Kilo-Org/kilocode/issues
