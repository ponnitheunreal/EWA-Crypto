# Elliot Wave Theory Documentation

## Overview

This module implements **Elliot Wave detection using price-action-based local extrema** (swing high/swing low identification).

## Detection Approach

### Swing Point Identification

The detector identifies swing points via rolling-window comparison:

- **Swing High**: Candle where `high[i] > high[i-window...i-1]` AND `high[i] > high[i+1...i+window]`
- **Swing Low**: Candle where `low[i] < low[i-window...i-1]` AND `low[i] < low[i+1...i+window]`

Default `swing_window = 5` bars (configurable).

### Wave Labeling

After extracting ordered swing points (alternating highs and lows), each two consecutive swing points forms a wave:

- **Wave Direction**: `"up"` if end_price > start_price, else `"down"`
- **Wave Number**: Cyclically assigned 1→2→3→4→5 then repeat (modulo 5)
- **Wave Types**:
  - **Impulse Waves**: Wave 1, Wave 3, Wave 5 (direction of the trend)
  - **Corrective Waves**: Wave 2, Wave 4 (counter-trend retracements)

### Wave Validation Rules

Basic validation applied to ensure pattern plausibility:

- Minimum wave duration: `min_wave_bars` bars (default 2)
- Fibonacci ratio compliance within tolerance:
  - Corrective waves (2,4) must retrace 23.6% - 78.6% of prior impulse
  - Impulse waves must show momentum (current move ≥ 0.618 × prior move)

## Wave Relationships

### Wave 2 Retracement
- Retraces **23.6% to 78.6%** of Wave 1
- Common zones: 38.2% (strong), 50% (psychological), 61.8% (golden)

### Wave 3 Extension
- Typically **161.8% or 261.8%** of Wave 1
- Wave 3 rarely shortest; often longest

### Wave 4 Retracement
- Retraces **23.6% to 38.2%** of Wave 3
- Shallower than Wave 2
- Should not overlap Wave 1 territory in strict Elliott Wave

### Wave 5 Projection
- **61.8%, 100%, or 161.8%** of Wave 1
- Often equals Wave 1 length (100%)
- May extend to 161.8% in strong trends

## Data Structures

### `Wave` NamedTuple

```python
Wave(
    start_idx,      # pandas Timestamp of wave origin
    end_idx,        # pandas Timestamp of wave termination
    start_price,    # starting price
    end_price,      # ending price
    wave_num,       # 1, 2, 3, 4, or 5
    direction,      # "up" or "down"
    confidence      # 0.0 - 1.0 validation score
)
```

### `ElliotWaveDetector` Class

```python
detector = ElliotWaveDetector(
    swing_window=5,    # pivot detection sensitivity
    min_wave_bars=2,   # minimum bars per wave segment
    fib_tolerance=0.15 # ±15% allowed Fib ratio deviation
)

result = detector.detect(df)
waves = result["waves"]              # List[Wave]
current_wave = result["current_wave"] # Most recent Wave
```

## API Methods

| Method | Returns | Purpose |
|--------|---------|---------|
| `detect(df)` | `Dict` | Full detection → waves, swing points, current wave |
| `get_wave_by_number(waves, n)` | `Optional[Wave]` | Get most recent occurrence of wave number n |
| `is_impulse_wave(wave)` | `bool` | True if wave 1, 3, or 5 |
| `is_corrective_wave(wave)` | `bool` | True if wave 2 or 4 |

## Configuration Notes

- **Swing window size**: Larger values (7-10) reduce noise but delay detection.
- **Trend filter coupling**: Waves are analyzed in conjunction with EMA 21 trend direction.
- **Invalid patterns**: Failed wave count resets; new cycle begins.

## References

- *Elliott Wave Principle* by Frost & Prechter
- Implementation: Price-action swing detection (no zigzag indicator dependency)
