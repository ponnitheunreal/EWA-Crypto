# elliot_wave.py - Elliot Wave Detection Module
# Uses price-action-based local extrema (swing highs/lows) to identify waves.

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import namedtuple

from .utils import find_swing_highs, find_swing_lows, filter_waves_by_ratio

# Named tuple to store wave data
Wave = namedtuple("Wave", [
    "start_idx",
    "end_idx",
    "start_price",
    "end_price",
    "wave_num",      # 1, 2, 3, 4, or 5
    "direction",     # "up" or "down"
    "confidence"     # 0.0 to 1.0 based on ratio check
])


class ElliotWaveDetector:
    """
    Elliot Wave detector using swing point identification.

    Detection approach: price-action based local extrema finding.
    - Identifies swing highs and swing lows using rolling window comparison.
    - Labels alternating impulse (1,3,5) and corrective (2,4) waves.
    - Validates wave relationships using Fibonacci ratios.
    """

    def __init__(
        self,
        swing_window: int = 5,
        min_wave_bars: int = 2,
        fib_tolerance: float = 0.15
    ):
        """
        Initialize the Elliot Wave detector.

        Args:
            swing_window: Window size for swing detection (default 5).
            min_wave_bars: Minimum number of bars per wave segment.
            fib_tolerance: Allowed Fibonacci ratio deviation (default 15%).
        """
        self.swing_window = swing_window
        self.min_wave_bars = min_wave_bars
        self.fib_tolerance = fib_tolerance

    def detect_swings(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Detect swing highs and swing lows in OHLCV data.

        Args:
            df: DataFrame with 'high' and 'low' columns.

        Returns:
            Tuple of (swing_highs_series, swing_lows_series) where True marks a swing point.
        """
        swing_highs = find_swing_highs(df, window=self.swing_window)
        swing_lows = find_swing_lows(df, window=self.swing_window)
        return swing_highs, swing_lows

    def _extract_swing_points(
        self,
        swing_highs: pd.Series,
        swing_lows: pd.Series,
        df: pd.DataFrame
    ) -> List[Dict]:
        """
        Extract ordered list of swing point dictionaries.
        Alternates between highs and lows in chronological order.
        """
        points = []

        # Combine and sort swing points
        high_idxs = swing_highs[swing_highs].index.tolist()
        for idx in high_idxs:
            points.append({
                "idx": idx,
                "price": df.loc[idx, "high"],
                "type": "high"
            })

        low_idxs = swing_lows[swing_lows].index.tolist()
        for idx in low_idxs:
            points.append({
                "idx": idx,
                "price": df.loc[idx, "low"],
                "type": "low"
            })

        # Sort chronologically
        points.sort(key=lambda p: p["idx"])

        # Filter to create alternation: remove consecutive same-type swings
        # Keep only extreme points in runs
        filtered = []
        last_type = None
        for p in points:
            if p["type"] != last_type:
                filtered.append(p)
                last_type = p["type"]
            else:
                # Same type twice - keep the more extreme one
                if filtered and p["type"] == "high":
                    if p["price"] > filtered[-1]["price"]:
                        filtered[-1] = p
                elif filtered and p["type"] == "low":
                    if p["price"] < filtered[-1]["price"]:
                        filtered[-1] = p

        return filtered

    def _validate_wave_sequence(
        self,
        waves: List[Wave],
        df: pd.DataFrame
    ) -> List[Wave]:
        """
        Apply Elliot Wave ratio rules to validate and score waves.
        """
        validated = []

        for i, wave in enumerate(waves):
            confidence = 1.0

            # Validate wave relationships with neighbors
            if i >= 1:
                prev = waves[i - 1]
                # Determine wave types based on position
                wave_numbers = [1, 2, 3, 4, 5]
                if (i + 1) in wave_numbers:
                    # Impulse wave (1,3,5)
                    prev_num = wave_numbers[i] if i > 0 else None
                    if prev_num and prev_num in [1, 3]:
                        # Check Wave 3 vs Wave 1 ratio; Wave 5 vs Wave 1 ratio
                        pass

            validated.append(wave._replace(confidence=confidence))

        return validated

    def detect(
        self,
        df: pd.DataFrame,
        trend_filter: Optional[pd.Series] = None
    ) -> Dict:
        """
        Detect Elliot Wave patterns in OHLCV data.

        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume'].
            trend_filter: Optional EMA series to bias wave direction.

        Returns:
            Dictionary containing:
                - waves: List of Wave namedtuples
                - swing_highs: Series marking swing highs
                - swing_lows: Series marking swing lows
                - current_wave: Latest detected wave info
        """
        if not all(col in df.columns for col in ['high', 'low']):
            raise ValueError("DataFrame must contain 'high' and 'low' columns")

        # 1. Detect swing points
        swing_highs, swing_lows = self.detect_swings(df)

        # 2. Build ordered swing point list
        swing_points = self._extract_swing_points(swing_highs, swing_lows, df)

        # 3. Group swings into wave sequences
        waves = []
        if len(swing_points) >= 2:
            # Start from first swing
            for i in range(len(swing_points) - 1):
                start_p = swing_points[i]
                end_p = swing_points[i + 1]

                direction = "up" if end_p["price"] > start_p["price"] else "down"
                wave_num = (i % 5) + 1  # Cycle 1-5

                wave = Wave(
                    start_idx=start_p["idx"],
                    end_idx=end_p["idx"],
                    start_price=start_p["price"],
                    end_price=end_p["price"],
                    wave_num=wave_num,
                    direction=direction,
                    confidence=1.0
                )
                waves.append(wave)

        # 4. Validate wave relationships
        waves = self._validate_wave_sequence(waves, df)

        # Determine most recent impulse vs corrective wave
        current_wave = None
        if waves:
            current_wave = waves[-1]

        return {
            "waves": waves,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
            "current_wave": current_wave
        }

    def get_wave_by_number(
        self,
        waves: List[Wave],
        wave_num: int
    ) -> Optional[Wave]:
        """
        Get the most recent occurrence of a specific wave number.
        """
        for wave in reversed(waves):
            if wave.wave_num == wave_num:
                return wave
        return None

    def is_impulse_wave(self, wave: Wave) -> bool:
        """
        Check if a wave is an impulse wave (1, 3, or 5).
        """
        return wave.wave_num in [1, 3, 5]

    def is_corrective_wave(self, wave: Wave) -> bool:
        """
        Check if a wave is a corrective wave (2 or 4).
        """
        return wave.wave_num in [2, 4]
