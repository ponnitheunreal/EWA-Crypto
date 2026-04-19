# fibonacci.py - Fibonacci Retracement and Extension Levels Module

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class FibonacciLevels:
    """
    Fibonacci retracement and extension level calculator for trading.

    Standard ratios sourced from Elliott Wave Theory:
    - Retracement: 0.236, 0.382, 0.5, 0.618, 0.786, 1.0
    - Extension: 1.0, 1.618, 2.618, 4.236
    """

    # Standard Fibonacci ratios
    RETRACEMENT_RATIOS = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    EXTENSION_RATIOS = [1.0, 1.618, 2.618, 4.236]

    def __init__(
        self,
        retracement_ratios: Optional[List[float]] = None,
        extension_ratios: Optional[List[float]] = None
    ):
        """
        Initialize Fibonacci levels calculator.

        Args:
            retracement_ratios: Custom retracement ratios (defaults to standard set).
            extension_ratios: Custom extension ratios (defaults to standard set).
        """
        self.retracement_ratios = retracement_ratios or self.RETRACEMENT_RATIOS
        self.extension_ratios = extension_ratios or self.EXTENSION_RATIOS

    def calculate_retracements(
        self,
        swing_high: float,
        swing_low: float,
        direction: str = "bullish"
    ) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels between a swing high and swing low.

        Args:
            swing_high: The high price of the move (must be > swing_low).
            swing_low: The low price of the move (must be < swing_high).
            direction: "bullish" for uptrend retracements, "bearish" for downtrend.

        Returns:
            Dictionary mapping level names to price values.
        """
        if swing_high <= swing_low:
            raise ValueError("swing_high must be greater than swing_low")

        levels = {}

        if direction == "bullish":
            # Price retraces down from high toward low
            for ratio in self.retracement_ratios:
                level_name = f"R{int(ratio * 100)}"
                levels[level_name] = swing_high - (swing_high - swing_low) * ratio
        else:  # bearish
            # Price retraces up from low toward high
            for ratio in self.retracement_ratios:
                level_name = f"R{int(ratio * 100)}"
                levels[level_name] = swing_low + (swing_high - swing_low) * ratio

        return levels

    def calculate_extensions(
        self,
        start: float,
        end: float,
        direction: str = "long"
    ) -> Dict[str, float]:
        """
        Calculate Fibonacci extension/projection levels.

        Args:
            start: Starting price of A-B move.
            end: Ending price of A-B move.
            direction: "long" for bullish targets, "short" for bearish targets.

        Returns:
            Dictionary mapping extension level names to price values.
        """
        move = end - start

        levels = {}
        for ratio in self.extension_ratios:
            if ratio == 1.0:
                level_name = "FE0"  # 100% equal move
            elif ratio == 1.618:
                level_name = "FE1"  # First target
            elif ratio == 2.618:
                level_name = "FE2"  # Second target
            else:
                level_name = f"FE{ratio:.3f}"

            if direction == "long":
                levels[level_name] = end + move * ratio
            else:
                levels[level_name] = end - move * ratio

        return levels

    def is_price_at_support(
        self,
        price: float,
        retracements: Dict[str, float],
        tolerance: float = 0.005
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if price is at or near a Fibonacci support/resistance level.

        Args:
            price: Current market price.
            retracements: Dictionary of retracement levels.
            tolerance: Allowed deviation as decimal (default 0.5%).

        Returns:
            Tuple of (is_at_level, level_name) where level_name is the nearest level.
        """
        if not retracements:
            return False, None

        nearest_level = None
        nearest_distance = float('inf')

        for level_name, level_price in retracements.items():
            distance = abs(price - level_price) / level_price
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_level = level_name

        is_at_level = nearest_distance <= tolerance
        return is_at_level, nearest_level

    def cluster_strength(
        self,
        price: float,
        retracements: Dict[str, float],
        extensions: Optional[Dict[str, float]] = None,
        tolerance: float = 0.01
    ) -> Tuple[float, List[str]]:
        """
        Calculate confluence strength of price near multiple Fibonacci levels.

        Args:
            price: Current market price.
            retracements: Retracement level dictionary.
            extensions: Optional extension level dictionary.
            tolerance: Search radius as decimal (default 1%).

        Returns:
            Tuple of (strength_score, nearby_level_names).
            Strength is 0.0-1.0 based on number of levels within tolerance.
        """
        nearby_levels = []

        for level_name, level_price in retracements.items():
            if abs(price - level_price) / level_price <= tolerance:
                nearby_levels.append(level_name)

        if extensions:
            for level_name, level_price in extensions.items():
                if abs(price - level_price) / level_price <= tolerance:
                    nearby_levels.append(level_name)

        # Strength increases with cluster density (max 1.0)
        strength = min(1.0, len(nearby_levels) * 0.25)
        return strength, nearby_levels
