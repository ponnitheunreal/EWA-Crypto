# Fibonacci Levels Documentation

## Overview

This module provides Fibonacci retracement and extension level calculations for the Elliot Wave Trading Indicator.

## Standard Ratios

### Retracement Levels

| Level Name | Ratio | Description |
|-----------|-------|-------------|
| R23.6 | 0.236 | Minor support/resistance |
| R38.2 | 0.382 | Strong support/resistance |
| R50 | 0.500 | Psychological level |
| R61.8 | 0.618 | Golden ratio |
| R78.6 | 0.786 | Deep retracement zone |
| R100 | 1.0 | Full retracement |

### Extension Levels

| Level Name | Ratio | Description |
|-----------|-------|-------------|
| FE0 | 1.000 | Equal move (100%) |
| FE1 | 1.618 | First target (61.8% extension) |
| FE2 | 2.618 | Second target (161.8% extension) |
| FE3 | 4.236 | Third target (323.6% extension) |

## Core Methods

### `calculate_retracements(swing_high, swing_low, direction)`

Calculates retracement levels between two swing points.

**Parameters:**
- `swing_high` (float): High price of the move
- `swing_low` (float): Low price of the move
- `direction` (str): `"bullish"` or `"bearish"`

**Returns:**
`Dict[str, float]` - Mapping of level names to price values

**Formula:**
```
Bullish: Level = High - (High - Low) × Ratio
Bearish: Level = Low + (High - Low) × Ratio
```

### `calculate_extensions(start, end, direction)`

Calculates Fibonacci extension targets for profit projection.

**Parameters:**
- `start` (float): Starting price of A-B move
- `end` (float): Ending price of A-B move
- `direction` (str): `"long"` or `"short"`

**Returns:**
`Dict[str, float]` - Mapping of extension level names to target prices

**Formula:**
```
Long:  Target = End + (End - Start) × Ratio
Short: Target = End - (End - Start) × Ratio
```

### `is_price_at_support(price, retracements, tolerance)`

Checks if current price is near a Fibonacci level.

**Returns:**
`(bool, Optional[str])` - (is_at_level, nearest_level_name)

### `cluster_strength(price, retracements, extensions, tolerance)`

Calculates confluence strength when price clusters near multiple Fib levels.

**Returns:**
`(float, List[str])` - (strength_score_0_to_1, list_of_nearby_levels)

## Usage Example

```python
from src.fibonacci import FibonacciLevels

fib = FibonacciLevels()

# Uptrend retracements
levels = fib.calculate_retracements(
    swing_high=50000,
    swing_low=45000,
    direction="bullish"
)
# Returns: {"R23.6": 49050.0, "R38.2": 48550.0, ...}

# Extension targets for profit-taking
targets = fib.calculate_extensions(
    start=45000,
    end=50000,
    direction="long"
)
# Returns: {"FE0": 55000, "FE1": 58090, "FE2": 63045, ...}
```

## Notes

- Ratios are stored as class constants and can be customized at initialization.
- Tolerance parameters are expressed as decimal ratios (0.01 = 1%).
- Level names follow convention: `R` for retracement (R38.2), `FE` for extension (FE1).
