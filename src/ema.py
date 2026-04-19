# ema.py - Exponential Moving Average (EMA) Calculation Module

import pandas as pd
import numpy as np


class EMA:
    """
    Exponential Moving Average (EMA) calculator.

    Formula: EMA_today = (Close_today × k) + (EMA_yesterday × (1 - k))
    where k = 2 / (N + 1) and N = period.
    """

    def __init__(self, period: int = 21):
        """
        Initialize EMA calculator with specified period.

        Args:
            period: The period for EMA calculation (default: 21).
        """
        if period < 1:
            raise ValueError("Period must be >= 1")
        self.period = period
        self.k = 2.0 / (period + 1)

    def calculate(self, closes: pd.Series) -> pd.Series:
        """
        Calculate EMA values for a series of closing prices.

        Args:
            closes: pandas Series of closing prices.

        Returns:
            pandas Series with EMA values.
        """
        ema_values = pd.Series(index=closes.index, dtype=float)

        # Initialize first EMA as first close (simple method)
        if len(closes) > 0:
            ema_values.iloc[0] = closes.iloc[0]

        # Calculate EMA iteratively
        for i in range(1, len(closes)):
            if pd.isna(closes.iloc[i]):
                ema_values.iloc[i] = ema_values.iloc[i - 1]
            else:
                ema_values.iloc[i] = (closes.iloc[i] * self.k) + \
                                     (ema_values.iloc[i - 1] * (1 - self.k))

        return ema_values

    def calculate_sma(self, closes: pd.Series) -> pd.Series:
        """
        Calculate Simple Moving Average for reference.
        """
        return closes.rolling(window=self.period).mean()

    def trend_direction(self, price_series: pd.Series, ema_series: pd.Series) -> pd.Series:
        """
        Determine trend direction based on price vs EMA relationship.

        Returns:
            Series with values: 1 (bullish/above EMA), -1 (bearish/below EMA), 0 (neutral)
        """
        direction = pd.Series(0, index=price_series.index)

        # Bullish: price > EMA
        direction[price_series > ema_series] = 1

        # Bearish: price < EMA
        direction[price_series < ema_series] = -1

        return direction
