# API Reference

## `CryptoElliotWaveIndicator`

Main indicator class. Call `analyze()` on OHLCV data to compute all outputs.

### Constructor

```python
CryptoElliotWaveIndicator(
    ema_period=21,             # EMA period for trend filter
    swing_window=5,            # Swing detection sensitivity
    fib_retracements=None,     # Optional custom ratios
    min_confidence=0.6         # Signal minimum confidence
)
```

### Methods

#### `analyze(df: pd.DataFrame) -> Dict`

Run full analysis pipeline. Returns dictionary with keys:

| Key | Type | Description |
|-----|------|-------------|
| `ema` | `pd.Series` | EMA 21 values |
| `trend` | `pd.Series` | 1 (bullish), -1 (bearish), 0 (neutral) |
| `swing_highs` | `pd.Series` | Boolean mask of swing high points |
| `swing_lows` | `pd.Series` | Boolean mask of swing low points |
| `waves` | `List[Wave]` | All detected waves in dataset |
| `current_wave` | `Optional[Wave]` | Most recently forming wave |
| `signals` | `pd.DataFrame` | Generated BUY/SELL signals |
| `retracements` | `Dict[str, float]` | Latest Fibonacci retracement levels |
| `extensions` | `Dict[str, float]` | Latest Fibonacci extension targets |

#### `get_latest_signal(df) -> Optional[Signal]`

Convenience method returning only the most recent signal object or `None`.

#### `get_support_resistance(df, lookback=20) -> Dict`

Returns current support/resistance levels derived from recent swings and Fib zones.

---

## Component Classes

### `EMA`

```python
ema = EMA(period=21)
ema_values = ema.calculate(closes: pd.Series) -> pd.Series
trend = ema.trend_direction(price_series, ema_series) -> pd.Series  # 1/-1/0
```

### `FibonacciLevels`

```python
fib = FibonacciLevels()

retracements = fib.calculate_retracements(
    swing_high, swing_low, direction="bullish"
) -> Dict[str, float]

extensions = fib.calculate_extensions(
    start, end, direction="long"
) -> Dict[str, float]

is_at_level, level_name = fib.is_price_at_support(
    price, retracements, tolerance=0.01
)

strength, nearby = fib.cluster_strength(
    price, retracements, extensions, tolerance=0.02
)
```

### `ElliotWaveDetector`

```python
detector = ElliotWaveDetector(swing_window=5)

result = detector.detect(df) -> Dict
waves = result["waves"]               # List[Wave]
current = result["current_wave"]      # Optional[Wave]
swing_highs = result["swing_highs"]   # pd.Series[bool]
swing_lows = result["swing_lows"]     # pd.Series[bool]

# Wave helpers
wave_3 = detector.get_wave_by_number(waves, 3)
is_impulse = detector.is_impulse_wave(wave)
is_corrective = detector.is_corrective_wave(wave)
```

### `SignalGenerator`

```python
gen = SignalGenerator(ema_period=21, min_confidence=0.6)

# Single-bar generation
signals = gen.generate(
    df, swing_highs, swing_lows, waves, current_wave
) -> List[Signal]

# Batch generation (full history)
signals_df = gen.batch_generate(df) -> pd.DataFrame
```

---

## Data Types

### `Wave` (namedtuple)

```python
Wave(
    start_idx: pd.Timestamp,
    end_idx: pd.Timestamp,
    start_price: float,
    end_price: float,
    wave_num: int,      # 1–5
    direction: str,     # "up" | "down"
    confidence: float   # 0.0–1.0
)
```

### `Signal` (dataclass)

```python
@dataclass
Signal:
    timestamp: pd.Timestamp
    signal_type: str          # "BUY" | "SELL"
    price: float
    confidence: float         # 0.0–1.0
    wave_num: int
    fib_level: Optional[str]
    ema_trend: str
    reason: str
    stop_loss: Optional[float]
    take_profit: Optional[float]
```

---

## Constants

### Fibonacci Ratios (Customizable)

```python
FibonacciLevels.RETRACEMENT_RATIOS  # [0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
FibonacciLevels.EXTENSION_RATIOS   # [1.0, 1.618, 2.618, 4.236]
```

### Signal Engine Defaults

```python
SignalGenerator.SUPPORT_ZONES         # [0.382, 0.5, 0.618]
SignalGenerator.TAKE_PROFIT_RATIOS    # [1.618, 2.618]
SignalGenerator.STOP_MULTIPLIER       # 1.5 (ATR multiple)
```

---

## Example: Complete Workflow

```python
import pandas as pd
from src import CryptoElliotWaveIndicator

# Load OHLCV DataFrame
df = pd.read_csv("btc_4h.csv", index_col="timestamp", parse_dates=True)

# Initialize indicator
indicator = CryptoElliotWaveIndicator()

# Full analysis
results = indicator.analyze(df)

# Extract components
ema = results["ema"]
waves = results["waves"]
signals = results["signals"]

# Print latest signal
latest_signal = indicator.get_latest_signal(df)
if latest_signal:
    print(latest_signal)
    # Output: 2025-04-19 00:00:00: BUY (conf=0.75) @ 62340.50 ...
```
