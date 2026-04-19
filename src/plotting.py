# plotting.py — Professional Multi-Panel Chart Generator

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
import os

from .indicator import CryptoElliotWaveIndicator
from .elliot_wave import Wave
from .signals import Signal


class ProfessionalChartPlotter:
    """
    High-quality multi-panel chart for Elliot Wave analysis.

    Panels:
    - Top: Price (candlesticks + EMA + waves + Fib levels + signals)
    - Bottom: Volume (colored by direction)

    Output: High-resolution PNG with clear annotations.
    """

    # Color scheme
    C = {
        "price_up": "#26a69a",       # Teal green
        "price_down": "#ef5350",     # Red
        "ema": "#ff9800",            # Orange
        "wave1": "#1976d2",          # Blue
        "wave2": "#f57c00",          # Orange
        "wave3": "#388e3c",          # Green
        "wave4": "#d32f2f",          # Red
        "wave5": "#7b1fa2",          # Purple
        "buy": "#4caf50",            # Green
        "sell": "#f44336",           # Red
        "entry": "#ffd700",          # Gold
        "sl": "#f44336",             # Red
        "tp": "#4caf50",             # Green
        "fib_ret": "#7986cb",        # Indigo
        "fib_ext": "#ba68c8",        # Purple
        "support": "#4caf50",
        "resistance": "#f44336",
        "bg": "#ffffff",
        "grid": "#e0e0e0",
        "text": "#212121",
    }

    def __init__(
        self,
        indicator: CryptoElliotWaveIndicator,
        style: str = "seaborn-v0_8-whitegrid",
        figsize: Tuple[int, int] = (22, 14),
    ):
        """
        Initialize professional plotter.

        Args:
            indicator: CryptoElliotWaveIndicator instance.
            style: Matplotlib style name.
            figsize: Figure size (width, height) in inches.
        """
        self.indicator = indicator
        self.figsize = figsize
        self.style = style
        plt.style.use(style)

    def _index_to_int(self, df: pd.DataFrame, timestamps: pd.DatetimeIndex) -> List[int]:
        """Convert timestamps to integer positions in DataFrame."""
        return [df.index.get_loc(ts) for ts in timestamps if ts in df.index]

    def _plot_price_panel(self, ax: plt.Axes, df: pd.DataFrame, signals_df: pd.DataFrame,
                         latest_signal: Optional[Signal], waves: List[Wave],
                         retracements: Dict[str, float], extensions: Dict[str, float],
                         support_resistance: Dict[str, List[float]], timeframe: str) -> None:
        """Main price chart with all overlays."""

        n_bars = len(df)
        x = np.arange(n_bars)

        # --- Candlesticks ---
        bullish = df["close"] >= df["open"]
        bearish = df["close"] < df["open"]

        # Body
        body_bull = df.loc[bullish, "close"].values - df.loc[bullish, "open"].values
        body_bear = df.loc[bearish, "open"].values - df.loc[bearish, "close"].values
        body_center_bull = (df.loc[bullish, "open"].values + df.loc[bullish, "close"].values) / 2
        body_center_bear = (df.loc[bearish, "open"].values + df.loc[bearish, "close"].values) / 2

        ax.bar(x[bullish], body_bull, bottom=df.loc[bullish, "open"].values,
               color=self.C["price_up"], width=0.7, alpha=0.9, edgecolor=self.C["price_up"], linewidth=0.5)
        ax.bar(x[bearish], body_bear, bottom=df.loc[bearish, "close"].values,
               color=self.C["price_down"], width=0.7, alpha=0.9, edgecolor=self.C["price_down"], linewidth=0.5)

        # Wicks
        ax.vlines(x[bullish], df.loc[bullish, "low"].values, df.loc[bullish, "high"].values,
                  color=self.C["price_up"], linewidth=1, alpha=0.6)
        ax.vlines(x[bearish], df.loc[bearish, "low"].values, df.loc[bearish, "high"].values,
                  color=self.C["price_down"], linewidth=1, alpha=0.6)

        # --- EMA 21 ---
        ema_vals = self.indicator.ema.calculate(df["close"])
        ax.plot(x, ema_vals.values, color=self.C["ema"], linewidth=2.5,
                linestyle="--", label="EMA 21", alpha=0.9, zorder=6)

        # --- Elliot Waves (last 4 for clarity) ---
        recent_waves = waves[-4:] if len(waves) > 4 else waves
        for wave in recent_waves:
            color_key = f"wave{wave.wave_num}"
            color = self.C.get(color_key, "#000000")
            try:
                start_pos = df.index.get_loc(wave.start_idx)
                end_pos = df.index.get_loc(wave.end_idx)
            except KeyError:
                continue

            x_seg = np.arange(start_pos, end_pos + 1)
            y_seg = df["close"].iloc[start_pos:end_pos + 1].values

            ax.plot(x_seg, y_seg, color=color, linewidth=3.5, marker="o",
                    markersize=6, markerfacecolor=color, markeredgecolor="white",
                    markeredgewidth=1, zorder=7, label=f"W{wave.wave_num}")

            # Wave label at start
            start_y = df["close"].iloc[start_pos]
            y_offset = -15 if wave.direction == "down" else 15
            ax.annotate(f"W{wave.wave_num}", xy=(start_pos, start_y),
                       xytext=(0, y_offset), textcoords="offset points",
                       fontsize=9, fontweight="bold", color=color,
                       ha="center", arrowprops=dict(arrowstyle="-|>", color=color, alpha=0.6))

        # --- Fibonacci Levels ---
        last_x = n_bars - 1
        for name, price in retracements.items():
            ax.axhline(y=price, color=self.C["fib_ret"], linestyle=":", linewidth=1.5, alpha=0.5)
            ax.text(n_bars + 5, price, f" {name}", va="center", fontsize=9,
                   color=self.C["fib_ret"], fontweight="bold", alpha=0.8,
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, edgecolor="none"))

        for name, price in extensions.items():
            ax.axhline(y=price, color=self.C["fib_ext"], linestyle="-.", linewidth=1.5, alpha=0.5)
            ax.text(n_bars + 5, price, f" {name}", va="center", fontsize=9,
                   color=self.C["fib_ext"], fontweight="bold", alpha=0.8,
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, edgecolor="none"))

        # --- Historical Signals (last 5) ---
        if not signals_df.empty:
            for idx, row in signals_df.tail(5).iterrows():
                try:
                    x_pos = df.index.get_loc(idx)
                except KeyError:
                    continue
                price = row["price"]
                color = self.C["buy"] if row["signal"] == "BUY" else self.C["sell"]
                marker = "^" if row["signal"] == "BUY" else "v"
                size = 120 if row.get("confidence", 0) >= 0.8 else 90
                ax.scatter(x_pos, price, marker=marker, color=color, s=size,
                          zorder=12, edgecolors="black", linewidth=2, alpha=0.9)
                ax.annotate(f"{row['signal']}\n{row['confidence']:.0%}",
                           xy=(x_pos, price), xytext=(0, 18 if row["signal"] == "BUY" else -22),
                           textcoords="offset points", ha="center", fontsize=8,
                           color=color, fontweight="bold",
                           arrowprops=dict(arrowstyle="->", color=color, alpha=0.6, linewidth=1.5))

        # --- Latest Signal: Entry, TP, SL ---
        if latest_signal:
            try:
                entry_x = n_bars - 1
            except:
                entry_x = last_x

            entry_price = latest_signal.price

            # Entry star
            ax.scatter(entry_x, entry_price, marker="*", color=self.C["entry"],
                      s=350, zorder=20, edgecolors="black", linewidth=3)
            ax.text(entry_x, entry_price * 1.008, f"ENTRY ${entry_price:,.0f}",
                   ha="center", fontsize=11, fontweight="bold", color=self.C["entry"])

            # Stop Loss
            if latest_signal.stop_loss:
                ax.axhline(y=latest_signal.stop_loss, color=self.C["sl"],
                          linestyle="--", linewidth=3, alpha=0.8, zorder=8)
                ax.text(entry_x, latest_signal.stop_loss * 0.992,
                       f"SL ${latest_signal.stop_loss:,.0f}",
                       ha="center", va="top", fontsize=10, fontweight="bold",
                       color=self.C["sl"],
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                alpha=0.95, edgecolor=self.C["sl"]))

            # Take Profit
            if latest_signal.take_profit:
                ax.axhline(y=latest_signal.take_profit, color=self.C["tp"],
                          linestyle="--", linewidth=3, alpha=0.8, zorder=8)
                ax.text(entry_x, latest_signal.take_profit * 1.008,
                       f"TP ${latest_signal.take_profit:,.0f}",
                       ha="center", va="bottom", fontsize=10, fontweight="bold",
                       color=self.C["tp"],
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                alpha=0.95, edgecolor=self.C["tp"]))

        # --- Support/Resistance ---
        if support_resistance:
            for level in support_resistance.get("support", []):
                ax.axhline(y=level, color=self.C["support"], linestyle=":", linewidth=1.5, alpha=0.4)
            for level in support_resistance.get("resistance", []):
                ax.axhline(y=level, color=self.C["resistance"], linestyle=":", linewidth=1.5, alpha=0.4)

        # --- Axis formatting ---
        ax.set_ylabel("Price (USDT)", fontsize=12, fontweight="bold", color=self.C["text"])
        ax.tick_params(axis='both', labelsize=10)

        # X-axis tick labels with date formatting
        tick_interval = max(1, n_bars // 15)
        tick_positions = np.arange(0, n_bars, tick_interval)
        if timeframe in ["1d", "D", "1w", "W"]:
            date_labels = [df.index[i].strftime("%Y-%m-%d") for i in tick_positions if i < n_bars]
        else:
            date_labels = [df.index[i].strftime("%m-%d %H:%M") for i in tick_positions if i < n_bars]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(date_labels, rotation=45, ha="right", fontsize=9)

        ax.grid(True, linestyle="--", alpha=0.2, color=self.C["grid"])
        ax.set_facecolor(self.C["bg"])
        for spine in ax.spines.values():
            spine.set_edgecolor(self.C["text"])

        # Title
        title = f"Elliot Wave Analysis — {timeframe.upper()}"
        if latest_signal:
            title += f" | {latest_signal.signal_type} @ ${latest_signal.price:,.0f} (conf={latest_signal.confidence:.0%})"
        ax.set_title(title, fontsize=14, fontweight="bold", pad=15, color=self.C["text"])

        # Legend
        legend_handles = [
            plt.Line2D([0], [0], color=self.C["ema"], linestyle="--", label="EMA 21", linewidth=2),
            plt.Rectangle((0,0),1,1, facecolor=self.C["price_up"], label="Bull"),
            plt.Rectangle((0,0),1,1, facecolor=self.C["price_down"], label="Bear"),
        ]
        if latest_signal:
            col = self.C["buy"] if latest_signal.signal_type == "BUY" else self.C["sell"]
            mark = "^" if latest_signal.signal_type == "BUY" else "v"
            legend_handles.append(plt.Line2D([0], [0], marker=mark, color=col,
                                            label=f"{latest_signal.signal_type} Signal",
                                            linestyle="None", markersize=10, markeredgecolor="black"))
        ax.legend(handles=legend_handles, loc="upper left", fontsize=9,
                 framealpha=0.95, ncol=4, frameon=True)

    def _plot_volume_panel(self, ax: plt.Axes, df: pd.DataFrame) -> None:
        """Volume bars below price."""
        if "volume" not in df.columns or df["volume"].sum() == 0:
            ax.set_visible(False)
            return

        n_bars = len(df)
        x = np.arange(n_bars)
        colors = [self.C["price_up"] if close >= open else self.C["price_down"]
                 for close, open in zip(df["close"], df["open"])]

        ax.bar(x, df["volume"], color=colors, width=0.7, alpha=0.6, edgecolor="none")
        ax.set_ylabel("Volume", fontsize=10, fontweight="bold", color=self.C["text"])
        ax.tick_params(axis='y', labelsize=8)
        ax.set_xlabel("Date", fontsize=11, fontweight="bold", color=self.C["text"])

        # X-ticks already synced from price panel
        tick_interval = max(1, n_bars // 15)
        tick_positions = np.arange(0, n_bars, tick_interval)
        ax.set_xticks(tick_positions)

        ax.grid(True, linestyle="--", alpha=0.2, color=self.C["grid"])
        ax.set_facecolor(self.C["bg"])

    def _add_signal_info_box(self, ax: plt.Axes, signal: Optional[Signal]) -> None:
        """Add info box in top-right corner."""
        if not signal:
            return

        info_lines = [
            f"Signal : {signal.signal_type}",
            f"Wave   : {signal.wave_num}",
            f"Entry  : ${signal.price:,.0f}",
        ]
        if signal.stop_loss:
            info_lines.append(f"SL     : ${signal.stop_loss:,.0f}")
        else:
            info_lines.append("SL     : N/A")
        if signal.take_profit:
            info_lines.append(f"TP     : ${signal.take_profit:,.0f}")
        else:
            info_lines.append("TP     : N/A")
        info_lines.append(f"Conf   : {signal.confidence:.0%}")

        info = "\n".join(info_lines)

        props = dict(boxstyle="round,pad=0.7", facecolor="white", alpha=0.95,
                    edgecolor=self.C["sl"] if signal.signal_type == "SELL" else self.C["tp"],
                    linewidth=2)

        ax.text(0.98, 0.95, info, transform=ax.transAxes, fontsize=10,
                verticalalignment="top", horizontalalignment="right",
                fontweight="bold", family="monospace", bbox=props)

    def plot(
        self,
        df: pd.DataFrame,
        output_path: str,
        symbol: str = "BTC/USDT",
        timeframe: str = "4h",
        dpi: int = 200,
        show_plot: bool = False
    ) -> str:
        """
        Generate and save professional multi-panel chart.

        Args:
            df: OHLCV DataFrame.
            output_path: Output PNG file path.
            symbol: Trading pair name for title.
            timeframe: Timeframe string (affects date format).
            dpi: Image resolution (default 200).
            show_plot: If True, display interactive window.

        Returns:
            Absolute path to saved PNG file.
        """
        results = self.indicator.analyze(df)
        waves = results["waves"]
        retracements = results.get("retracements", {})
        extensions = results.get("extensions", {})
        latest_signal = self.indicator.get_latest_signal(df)
        support_resistance = self.indicator.get_support_resistance(df, lookback=60)

        fig, (ax_price, ax_volume) = self._create_figure()

        # Price panel
        self._plot_price_panel(
            ax_price, df, results["signals"], latest_signal,
            waves, retracements, extensions, support_resistance, timeframe
        )

        # Volume panel
        self._plot_volume_panel(ax_volume, df)

        # Info box
        self._add_signal_info_box(ax_price, latest_signal)

        # Save
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
        if show_plot:
            plt.show()
        plt.close(fig)

        return os.path.abspath(output_path)

    def _create_figure(self) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
        """Create figure with price and volume subplots."""
        fig = plt.figure(figsize=self.figsize, constrained_layout=True)
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.05)
        ax_price = fig.add_subplot(gs[0, 0])
        ax_volume = fig.add_subplot(gs[1, 0], sharex=ax_price)
        return fig, (ax_price, ax_volume)


# Convenience function
def generate_chart(
    df: pd.DataFrame,
    indicator: CryptoElliotWaveIndicator,
    output_path: str,
    symbol: str = "BTC/USDT",
    timeframe: str = "4h",
    **kwargs
) -> str:
    """
    One-liner to generate professional chart.

    Example:
        indicator = CryptoElliotWaveIndicator()
        df = fetch_ohlcv("binance", "BTC/USDT", "1d", 500)
        path = generate_chart(df, indicator, "charts/daily.png", symbol="BTC/USDT", timeframe="1d")
    """
    plotter = ProfessionalChartPlotter(indicator)
    return plotter.plot(df=df, output_path=output_path, symbol=symbol,
                       timeframe=timeframe, **kwargs)
