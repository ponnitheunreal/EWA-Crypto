# signals.py - Buy/Sell Signal Generation Module

import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .ema import EMA
from .fibonacci import FibonacciLevels
from .elliot_wave import ElliotWaveDetector, Wave


@dataclass
class Signal:
    """
    Represents a trading signal with all relevant metadata.
    """
    timestamp: pd.Timestamp
    signal_type: str  # "BUY" or "SELL"
    price: float
    confidence: float  # 0.0 - 1.0
    wave_num: int
    fib_level: Optional[str] = None
    ema_trend: str = ""
    reason: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    def __str__(self) -> str:
        return (f"{self.timestamp}: {self.signal_type} (conf={self.confidence:.2f}) "
                f"@ {self.price:.2f} | Wave {self.wave_num} | {self.reason}")


class SignalGenerator:
    """
    Generates BUY/SELL signals based on confluence of:
    - EMA 21 trend direction
    - Elliot Wave position (Wave 3 or Wave 5 forming)
    - Price at Fibonacci support/resistance
    - Fibonacci extension projection
    """

    # Key Fibonacci retracement zones for entry
    SUPPORT_ZONES = [0.382, 0.5, 0.618]
    RESISTANCE_ZONES = [0.382, 0.5, 0.618]

    # Target extension ratios
    TAKE_PROFIT_RATIOS = [1.618, 2.618]

    # Stop-loss offset as multiple of recent ATR (default 1.5x)
    STOP_MULTIPLIER = 1.5

    def __init__(
        self,
        ema_period: int = 21,
        fib_ratios: Optional[List[float]] = None,
        min_confidence: float = 0.6
    ):
        """
        Initialize the signal generator.

        Args:
            ema_period: EMA period (default 21).
            fib_ratios: Custom Fibonacci retracement ratios.
            min_confidence: Minimum confidence threshold for signals.
        """
        self.ema = EMA(period=ema_period)
        self.fib = FibonacciLevels(retracement_ratios=fib_ratios)
        self.wave_detector = ElliotWaveDetector()
        self.min_confidence = min_confidence

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range for stop-loss placement.
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        return tr.rolling(window=period).mean()  # type: ignore

    def generate(
        self,
        df: pd.DataFrame,
        swing_highs: pd.Series,
        swing_lows: pd.Series,
        waves: List[Wave],
        current_wave: Optional[Wave]
    ) -> List[Signal]:
        """
        Generate trading signals for the latest bar.

        Args:
            df: OHLCV DataFrame.
            swing_highs: Series of detected swing highs.
            swing_lows: Series of detected swing lows.
            waves: List of all detected waves.
            current_wave: The most recent/current wave.

        Returns:
            List of Signal objects (typically 0-1 per bar).
        """
        if df.empty or current_wave is None:
            return []

        signals = []

        # Get latest data
        latest_idx = df.index[-1]
        latest_close = df["close"].iloc[-1]
        latest_ema = self.ema.calculate(df["close"]).iloc[-1]  # type: ignore

        # EMA trend
        ema_trend = "bullish" if latest_close > latest_ema else "bearish"

        # Find relevant Fibonacci retracements for recent impulse wave
        fib_retracements = {}
        # Get the previous impulse wave (Wave 1, 3 or 5)
        prev_impulse = None
        for wave in reversed(waves[:-1]):
            if wave.wave_num in [1, 3, 5]:
                prev_impulse = wave
                break

        if prev_impulse:
            start_price = prev_impulse.start_price
            end_price = prev_impulse.end_price

            # Direction of that impulse wave
            direction = "bullish" if end_price > start_price else "bearish"

            fib_retracements = self.fib.calculate_retracements(
                swing_high=max(start_price, end_price),
                swing_low=min(start_price, end_price),
                direction=direction
            )

        # Calculate Fibonacci extensions for targets
        fib_extensions = {}
        if prev_impulse:
            # Map ema_trend ("bullish"/"bearish") to desired extension direction
            ext_direction = "long" if ema_trend == "bullish" else "short"
            fib_extensions = self.fib.calculate_extensions(
                start=prev_impulse.start_price,
                end=prev_impulse.end_price,
                direction=ext_direction
            )

        # Check price proximity to Fib levels
        at_fib_level = False
        fib_level_name = None
        if fib_retracements:
            at_fib_level, fib_level_name = self.fib.is_price_at_support(
                latest_close, fib_retracements, tolerance=0.01
            )

        # --- BUY Signal Conditions ---
        if ema_trend == "bullish":
            is_impulse_wave = current_wave.wave_num in [3, 5]
            at_support = at_fib_level and fib_level_name is not None
            has_confluence = at_support  # Simplified: support zone = confluence

            if is_impulse_wave and at_support:
                confidence = 0.7
                if current_wave.wave_num == 3:
                    confidence += 0.1  # Wave 3 typically strongest

                # Check if price is also approaching an extension target
                if fib_extensions:
                    _, nearest_ext = self.fib.is_price_at_support(
                        latest_close, fib_extensions, tolerance=0.02
                    )
                    if nearest_ext:
                        confidence += 0.1

                if confidence >= self.min_confidence:
                    # Calculate stop-loss and take-profit
                    atr = self._calculate_atr(df).iloc[-1]
                    stop_loss = latest_close - (self.STOP_MULTIPLIER * atr)

                    tp_price = None
                    if fib_extensions:
                        # Use nearest extension above as target
                        targets = [p for p in fib_extensions.values() if p > latest_close]
                        if targets:
                            tp_price = min(targets)

                    signal = Signal(
                        timestamp=latest_idx,  # type: ignore
                        signal_type="BUY",
                        price=latest_close,
                        confidence=confidence,
                        wave_num=current_wave.wave_num,
                        fib_level=fib_level_name,
                        ema_trend=ema_trend,
                        reason=f"Wave {current_wave.wave_num} at Fib {fib_level_name} support, EMA bullish",
                        stop_loss=stop_loss,
                        take_profit=tp_price
                    )
                    signals.append(signal)

        # --- SELL Signal Conditions ---
        elif ema_trend == "bearish":
            is_impulse_wave = current_wave.wave_num in [3, 5]
            at_resistance = at_fib_level and fib_level_name is not None

            if is_impulse_wave and at_resistance:
                confidence = 0.7
                if current_wave.wave_num == 3:
                    confidence += 0.1

                if fib_extensions:
                    _, nearest_ext = self.fib.is_price_at_support(
                        latest_close, fib_extensions, tolerance=0.02
                    )
                    if nearest_ext:
                        confidence += 0.1

                if confidence >= self.min_confidence:
                    atr = self._calculate_atr(df).iloc[-1]
                    stop_loss = latest_close + (self.STOP_MULTIPLIER * atr)

                    tp_price = None
                    if fib_extensions:
                        targets = [p for p in fib_extensions.values() if p < latest_close]
                        if targets:
                            tp_price = max(targets)

                    signal = Signal(
                        timestamp=latest_idx,  # type: ignore
                        signal_type="SELL",
                        price=latest_close,
                        confidence=confidence,
                        wave_num=current_wave.wave_num,
                        fib_level=fib_level_name,
                        ema_trend=ema_trend,
                        reason=f"Wave {current_wave.wave_num} at Fib {fib_level_name} resistance, EMA bearish",
                        stop_loss=stop_loss,
                        take_profit=tp_price
                    )
                    signals.append(signal)

        return signals

    def batch_generate(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate signals for all bars in a DataFrame.

        Returns:
            DataFrame with signal columns appended.
        """
        signals_list = []

        # We need minimum bars for EMA and swing detection
        min_bars = max(50, self.ema.period + 10)

        for i in range(min_bars, len(df)):
            subset = df.iloc[:i + 1].copy()

            # Detect waves on rolling window
            result = self.wave_detector.detect(subset)
            waves = result["waves"]
            current = result["current_wave"]

            if current is None:
                continue

            # Generate signal
            sigs = self.generate(
                df=subset,
                swing_highs=result["swing_highs"],
                swing_lows=result["swing_lows"],
                waves=waves,
                current_wave=current
            )

            if sigs:
                for sig in sigs:
                    signals_list.append({
                        "timestamp": sig.timestamp,
                        "signal": sig.signal_type,
                        "confidence": sig.confidence,
                        "wave": sig.wave_num,
                        "fib_level": sig.fib_level,
                        "price": sig.price,
                        "stop_loss": sig.stop_loss,
                        "take_profit": sig.take_profit,
                        "reason": sig.reason
                    })

        if signals_list:
            return pd.DataFrame(signals_list).set_index("timestamp")
        return pd.DataFrame()
