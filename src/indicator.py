# indicator.py - Main Crypto Elliot Wave Trading Indicator API

import pandas as pd
from typing import Dict, Any, Optional, List

from .ema import EMA
from .fibonacci import FibonacciLevels
from .elliot_wave import ElliotWaveDetector, Wave
from .signals import SignalGenerator, Signal


class CryptoElliotWaveIndicator:
    """
    Unified indicator combining:
    - EMA 21 for trend filter
    - Elliot Wave detection via swing points
    - Fibonacci retracement/extension analysis
    - Buy/Sell signal generation with confluence logic

    Usage:
        indicator = CryptoElliotWaveIndicator()
        results = indicator.analyze(df)
        signals = results["signals"]
    """

    def __init__(
        self,
        ema_period: int = 21,
        swing_window: int = 5,
        fib_retracements: Optional[list] = None,
        min_confidence: float = 0.6
    ):
        """
        Initialize the complete Elliot Wave indicator system.

        Args:
            ema_period: EMA period for trend filter (default 21).
            swing_window: Window size for swing point detection (default 5).
            fib_retracements: Custom Fibonacci retracement ratios.
            min_confidence: Minimum confidence threshold for signals (0-1).
        """
        self.ema = EMA(period=ema_period)
        self.wave_detector = ElliotWaveDetector(swing_window=swing_window)
        self.fib = FibonacciLevels(retracement_ratios=fib_retracements)
        self.signal_generator = SignalGenerator(
            ema_period=ema_period,
            fib_ratios=fib_retracements,
            min_confidence=min_confidence
        )

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run full analysis on OHLCV data.

        Args:
            df: DataFrame with columns: open, high, low, close, volume (volume optional).

        Returns:
            Dictionary containing:
                - ema: Series of EMA 21 values
                - trend: Series with values 1 (bullish), -1 (bearish), 0 (neutral)
                - swing_highs: Boolean Series marking swing high points
                - swing_lows: Boolean Series marking swing low points
                - waves: List of detected Wave objects
                - current_wave: Most recent Wave object
                - signals: DataFrame of BUY/SELL signals
                - retracements: Dict of latest Fibonacci retracement levels
                - extensions: Dict of latest Fibonacci extension levels
        """
        if df.empty:
            return {}

        # Validate required columns
        required_cols = ["open", "high", "low", "close"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")

        # 1. Calculate EMA and trend
        ema_series = self.ema.calculate(df["close"])  # type: ignore
        trend_series = self.ema.trend_direction(df["close"], ema_series)  # type: ignore

        # 2. Detect Elliot Waves
        wave_result = self.wave_detector.detect(df)
        waves = wave_result["waves"]
        current_wave = wave_result["current_wave"]

        # 3. Calculate latest Fibonacci retracements/extensions
        retracements = {}
        extensions = {}
        if len(waves) >= 2:
            # Find most recent impulse wave (1,3,5)
            recent_impulse = None
            for wave in reversed(waves):
                if wave.wave_num in [1, 3, 5]:
                    recent_impulse = wave
                    break

            if recent_impulse:
                direction = "bullish" if recent_impulse.end_price > recent_impulse.start_price else "bearish"
                high = max(recent_impulse.start_price, recent_impulse.end_price)
                low = min(recent_impulse.start_price, recent_impulse.end_price)

                retracements = self.fib.calculate_retracements(
                    swing_high=high,
                    swing_low=low,
                    direction=direction
                )
                extensions = self.fib.calculate_extensions(
                    start=recent_impulse.start_price,
                    end=recent_impulse.end_price,
                    direction=direction
                )

        # 4. Generate signals
        signal_df = self.signal_generator.batch_generate(df)

        return {
            "ema": ema_series,
            "trend": trend_series,
            "swing_highs": wave_result["swing_highs"],
            "swing_lows": wave_result["swing_lows"],
            "waves": waves,
            "current_wave": current_wave,
            "signals": signal_df,
            "retracements": retracements,
            "extensions": extensions,
        }

    def get_latest_signal(
        self,
        df: pd.DataFrame,
        higher_tf_df: Optional[pd.DataFrame] = None
    ) -> Optional[Signal]:
        """
        Get the most recent signal only.

        Args:
            df: OHLCV DataFrame for the current (lower) timeframe.
            higher_tf_df: Optional OHLCV DataFrame for a higher timeframe
                          (e.g., daily if current is 4H) to assess trend bias.

        Returns:
            Signal object with enriched context, or None if no signal.
        """
        results = self.analyze(df)
        signal_df = results.get("signals", pd.DataFrame())

        if not signal_df.empty:
            latest = signal_df.iloc[-1]
            
            # Base Signal object (existing fields)
            signal = Signal(
                timestamp=latest.name,
                signal_type=latest["signal"],
                price=latest["price"],
                confidence=latest["confidence"],
                wave_num=int(latest["wave"]),
                fib_level=latest["fib_level"],
                ema_trend="bullish" if latest["signal"] == "BUY" else "bearish",
                reason=latest["reason"],
                stop_loss=latest["stop_loss"],
                take_profit=latest["take_profit"]
            )

            # --- 1. Signal Category (based on distance from entry to current price) ---
            current_price = df["close"].iloc[-1]
            distance_pct = abs(signal.price - current_price) / current_price * 100
            if distance_pct <= 3:
                signal.signal_category = "ACTIVE_TRADE"
            elif distance_pct <= 8:
                signal.signal_category = "SETUP"
            else:
                signal.signal_category = "INVALID"

            # --- 2. Trend Context (HTF vs LTF alignment) ---
            bias = self._determine_bias(higher_tf_df) if higher_tf_df is not None else None
            if bias:
                if (bias == "BULLISH" and signal.signal_type == "BUY") or \
                   (bias == "BEARISH" and signal.signal_type == "SELL"):
                    signal.trend_context = "TREND_ALIGNED"
                else:
                    signal.trend_context = "COUNTER_TREND"
            else:
                signal.trend_context = "NONE"

            # --- 3. Confidence Adjustment ---
            conf = signal.confidence
            if signal.trend_context == "COUNTER_TREND":
                conf -= 0.20
            if signal.signal_category != "ACTIVE_TRADE":
                conf -= 0.15
            # Wave count penalty: unusually high wave count suggests noisy/unclear structure
            total_waves = len(results.get("waves", []))
            if total_waves > 15:
                conf -= 0.10
            # Clamp between 40% and 90%
            signal.confidence = max(0.40, min(0.90, conf))

            return signal
        return None

    def get_support_resistance(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> Dict[str, List[float]]:
        """
        Identify current support and resistance levels based on
        recent swing points and Fibonacci zones.

        Args:
            df: OHLCV DataFrame.
            lookback: Number of recent bars to consider.

        Returns:
            Dictionary with 'support' and 'resistance' lists of price levels.
        """
        result = self.analyze(df.tail(lookback * 3))
        retracements = result.get("retracements", {})
        extensions = result.get("extensions", {})

        current_price = df["close"].iloc[-1]
        support = []
        resistance = []

        # Retracement levels
        for level_name, level_price in retracements.items():
            if level_price < current_price:
                support.append(level_price)
            elif level_price > current_price:
                resistance.append(level_price)

        # Extension levels (additional S/R)
        for level_name, level_price in extensions.items():
            if level_price < current_price:
                support.append(level_price)
            elif level_price > current_price:
                resistance.append(level_price)

        return {
            "support": sorted(support, reverse=True)[:3],
            "resistance": sorted(resistance)[:3]
        }

    def _determine_bias(self, df: pd.DataFrame) -> Optional[str]:
        """
        Determine the trend bias (BULLISH/BEARISH/NEUTRAL) for a given DataFrame.
        Uses EMA trend direction as a simple, robust proxy.

        Args:
            df: OHLCV DataFrame.

        Returns:
            "BULLISH", "BEARISH", "NEUTRAL", or None if insufficient data.
        """
        if df.empty or "close" not in df.columns or len(df) < 2:
            return None
        try:
            ema_vals = self.ema.calculate(df["close"])
            trend_dir = self.ema.trend_direction(df["close"], ema_vals).iloc[-1]
            if trend_dir > 0:
                return "BULLISH"
            elif trend_dir < 0:
                return "BEARISH"
            else:
                return "NEUTRAL"
        except Exception:
            return None
