# utils.py - Helper functions for the Elliot Wave Trading Indicator

import pandas as pd
from typing import Tuple, Optional


def find_swing_highs(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """
    Identify swing high points in price data.
    A swing high is a candle where the high is greater than the high of
    the previous and next 'window' candles.
    """
    highs = df['high']
    swing_highs = pd.Series(False, index=df.index)

    for i in range(window, len(df) - window):
        current = highs.iloc[i]
        is_swing = all(current > highs.iloc[i - j] for j in range(1, window + 1)) and \
                   all(current > highs.iloc[i + j] for j in range(1, window + 1))
        swing_highs.iloc[i] = is_swing

    return swing_highs


def find_swing_lows(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """
    Identify swing low points in price data.
    A swing low is a candle where the low is lower than the low of
    the previous and next 'window' candles.
    """
    lows = df['low']
    swing_lows = pd.Series(False, index=df.index)

    for i in range(window, len(df) - window):
        current = lows.iloc[i]
        is_swing = all(current < lows.iloc[i - j] for j in range(1, window + 1)) and \
                   all(current < lows.iloc[i + j] for j in range(1, window + 1))
        swing_lows.iloc[i] = is_swing

    return swing_lows


def calculate_retracement_level(
    start: float,
    end: float,
    ratio: float
) -> float:
    """
    Calculate Fibonacci retracement level between two price points.
    For bullish move (start < end): retracement goes down from end.
    """
    return end - (end - start) * ratio


def calculate_extension_level(
    start: float,
    end: float,
    ratio: float,
    direction: str = "long"
) -> float:
    """
    Calculate Fibonacci extension/expansion level.
    For longs: projects target upward from end using A-B move.
    For shorts: projects target downward from end.
    """
    move = end - start
    if direction == "long":
        return end + move * ratio
    else:
        return end - move * ratio


def filter_waves_by_ratio(
    wave_start: float,
    wave_end: float,
    prev_wave_start: float,
    prev_wave_end: float,
    wave_type: str
) -> bool:
    """
    Check if a wave's price movement satisfies Fibonacci ratio requirements.

    Args:
        wave_start: Starting price of current wave
        wave_end: Ending price of current wave
        prev_wave_start: Starting price of previous wave
        prev_wave_end: Ending price of previous wave
        wave_type: "impulse" (wave 1,3,5) or "corrective" (wave 2,4)

    Returns:
        True if the wave satisfies ratio constraints
    """
    prev_move = abs(prev_wave_end - prev_wave_start)
    current_move = abs(wave_end - wave_start)

    if wave_type == "corrective":
        # Wave 2 / Wave 4 retrace 23.6% - 78.6% of previous impulse
        retracement = current_move / prev_move if prev_move != 0 else 0
        return 0.236 <= retracement <= 0.786
    else:
        # Impulse waves (1,3,5) - Wave 3 typically 1.618x+ Wave 1
        return current_move >= prev_move * 0.618
