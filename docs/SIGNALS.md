# Signals Documentation

## Overview

The signal engine combines **EMA 21 trend direction**, **Elliot Wave position**, and **Fibonacci confluence** to generate high-confidence BUY/SELL signals.

---

## BUY Signal Conditions

All four conditions must align:

1. **EMA 21 BULLISH** — Price > EMA 21 (trend filter)
2. **Wave 3 or Wave 5 forming** — Impulse wave in progress
3. **Price at Fibonacci support** — At or near 38.2%, 50%, or 61.8% retracement
4. **Confluence** — Price also approaching next Fibonacci extension target (FE1/FE2)

```
BUY = (trend == bullish) AND
      (wave_num in {3, 5}) AND
      (price_at_fib_retracement) AND
      (confluence_score ≥ threshold)
```

### Confidence Scoring

| Factor | +Confidence |
|--------|-------------|
| Wave 3 detected | +0.1 |
| Exact Fib level hit | +0.1 |
| Multiple Fib cluster | +0.1–0.25 |
| Near extension target | +0.1 |
| **Base confidence** | **0.7** |

Minimum threshold: **0.6**

---

## SELL Signal Conditions

1. **EMA 21 BEARISH** — Price < EMA 21
2. **Wave 3 or Wave 5 forming** — Downward impulse wave
3. **Price at Fibonacci resistance** — At retracement zone in downtrend
4. **Confluence** — Price at/approaching bearish extension target

```
SELL = (trend == bearish) AND
       (wave_num in {3, 5}) AND
       (price_at_fib_resistance) AND
       (confluence_score ≥ threshold)
```

---

## Stop-Loss & Take-Profit

### Stop-Loss
```
Stop = Current Price ± (1.5 × ATR(14))
```
- Longs: stop below entry
- Shorts: stop above entry

### Take-Profit
- Projected to nearest Fibonacci extension level
  - **FE1 (161.8%)** — Primary target
  - **FE2 (261.8%)** — Secondary target

---

## Signal Object

```python
@dataclass
Signal:
    timestamp: pd.Timestamp
    signal_type: str          # "BUY" or "SELL"
    price: float
    confidence: float         # 0.0 – 1.0
    wave_num: int             # 1–5
    fib_level: Optional[str]  # e.g. "R38.2", "R61.8"
    ema_trend: str            # "bullish" / "bearish"
    reason: str               # Human-readable rationale
    stop_loss: Optional[float]
    take_profit: Optional[float]
```

---

## API Usage

### Single-Bar Signal Generation

```python
from src.indicator import CryptoElliotWaveIndicator

indicator = CryptoElliotWaveIndicator()
result = indicator.analyze(latest_bar_df)

# Latest signal only
signal = indicator.get_latest_signal(df)
if signal:
    print(f"{signal.signal_type} @ {signal.price} (SL:{signal.stop_loss} TP:{signal.take_profit})")
```

### Batch Signal Generation

```python
# Generate all historical signals
signals_df = indicator.signal_generator.batch_generate(df)
# Returns DataFrame: index=timestamp, columns=[signal, confidence, wave, fib_level, ...]
```

---

## Risk Parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `STOP_MULTIPLIER` | 1.5 | ATR multiple for stop-distance |
| `min_confidence` | 0.6 | Minimum confidence threshold |
| `fib_tolerance` | 0.01 (1%) | Price deviation from exact Fib level allowed |

---

## Notes

- **Parallel filtering**: EMA trend is mandatory — never trade counter-trend.
- **Wave-only entries**: Only Wave 3 and Wave 5 qualify; Wave 1 is too early, Wave 2/4 are corrective.
- **Confluence requirement**: Price must be in a retracement zone; isolated wave signals are ignored.
- **False signal prevention**: Minimum confidence threshold filters weak setups.
