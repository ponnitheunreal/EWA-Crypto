# plotting.py — High-Resolution Professional Chart Generator

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple, List, Literal
from datetime import datetime
import os

from .indicator import CryptoElliotWaveIndicator
from .elliot_wave import Wave
from .signals import Signal


class HighResolutionPlotter:
    """
    High-resolution, publication-quality chart generator for Elliot Wave analysis.

    Features:
    - Default 300 DPI output (configurable up to 1200 DPI)
    - Vector export support (PDF, SVG, EPS)
    - Adaptive figure sizing based on data density
    - Dark and light themes
    - Intelligent label placement to prevent overlap
    - Multi-panel layout: price + volume + optional indicator panel
    - High-quality anti-aliased rendering

    Example:
        plotter = HighResolutionPlotter(indicator, theme="dark", dpi=300)
        plotter.plot(df, "charts/chart.png", format="png")
    """

    # Color palettes
    THEMES = {
        "light": {
            "price_up": "#26a69a",
            "price_down": "#ef5350",
            "ema": "#ff9800",
            "wave1": "#1976d2",
            "wave2": "#f57c00",
            "wave3": "#388e3c",
            "wave4": "#d32f2f",
            "wave5": "#7b1fa2",
            "buy": "#4caf50",
            "sell": "#f44336",
            "entry": "#ffd700",
            "sl": "#f44336",
            "tp": "#4caf50",
            "fib_ret": "#7986cb",
            "fib_ext": "#ba68c8",
            "support": "#4caf50",
            "resistance": "#f44336",
            "bg": "#ffffff",
            "grid": "#e0e0e0",
            "text": "#212121",
            "volume_up": (38/255, 166/255, 154/255, 0.6),
            "volume_down": (239/255, 83/255, 80/255, 0.6),
        },
        "dark": {
            "price_up": "#4db6ac",
            "price_down": "#ef5350",
            "ema": "#ffb74d",
            "wave1": "#64b5f6",
            "wave2": "#ffb74d",
            "wave3": "#81c784",
            "wave4": "#e57373",
            "wave5": "#ba68c8",
            "buy": "#66bb6a",
            "sell": "#ef5350",
            "entry": "#ffd700",
            "sl": "#ef5350",
            "tp": "#66bb6a",
            "fib_ret": "#7986cb",
            "fib_ext": "#ba68c8",
            "support": "#66bb6a",
            "resistance": "#ef5350",
            "bg": "#121212",
            "grid": "#333333",
            "text": "#e0e0e0",
            "volume_up": (77/255, 182/255, 172/255, 0.6),
            "volume_down": (239/255, 83/255, 80/255, 0.6),
        },
    }

    def __init__(
        self,
        indicator: CryptoElliotWaveIndicator,
        theme: Literal["light", "dark"] = "light",
        base_dpi: int = 300,
        figsize_scale: float = 1.0,
    ):
        """
        Initialize high-resolution plotter.

        Args:
            indicator: CryptoElliotWaveIndicator instance.
            theme: "light" or "dark" color scheme.
            base_dpi: Base DPI for raster output (min 150, recommended 300-600).
            figsize_scale: Scale factor for figure size (1.0 = default).
        """
        self.indicator = indicator
        self.theme = theme
        self.colors = self.THEMES[theme]
        self.base_dpi = max(150, min(base_dpi, 1200))  # clamp 150-1200
        self.figsize_scale = figsize_scale

        # Professional font settings
        plt.rcParams.update({
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 13,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.dpi": self.base_dpi,
            "savefig.dpi": self.base_dpi,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.3,
            "axes.facecolor": self.colors["bg"],
            "figure.facecolor": self.colors["bg"],
            "savefig.facecolor": self.colors["bg"],
            "savefig.edgecolor": "none",
            "axes.edgecolor": self.colors["text"],
            "axes.labelcolor": self.colors["text"],
            "xtick.color": self.colors["text"],
            "ytick.color": self.colors["text"],
            "text.color": self.colors["text"],
            "grid.color": self.colors["grid"],
            "grid.alpha": 0.2,
        })

    def _calculate_figure_size(self, n_bars: int, timeframe: str) -> Tuple[int, int]:
        """Auto-scale figure based on data density and timeframe."""
        # Base size
        base_width = 20
        base_height = 10

        # Adjust for timeframe - daily needs more width per bar
        if timeframe in ["1d", "D", "1w", "W"]:
            width_per_bar = 0.15  # wider spacing for daily
        else:
            width_per_bar = 0.08  # denser for intraday

        # Scale width by number of bars (capped to avoid excessive size)
        width = min(base_width + n_bars * width_per_bar, 40) * self.figsize_scale

        # Height scales slightly with density
        height_multiplier = 1.0 + min(n_bars / 500, 0.5)
        height = base_height * height_multiplier * self.figsize_scale

        return (int(width), int(height))

    def _create_figure(self, n_bars: int, timeframe: str) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
        """Create optimized figure with subplots."""
        width, height = self._calculate_figure_size(n_bars, timeframe)

        # Use constrained_layout for automatic spacing
        fig = plt.figure(figsize=(width, height), constrained_layout=True)
        fig.set_dpi(self.base_dpi)
        fig.set_facecolor(self.colors["bg"])

        # Create 2-row layout: price (75%), volume (25%)
        gs = fig.add_gridspec(
            2, 1,
            height_ratios=[4, 1],
            hspace=0.08,
            left=0.07,
            right=0.97,
            bottom=0.06,
            top=0.95
        )

        ax_price = fig.add_subplot(gs[0, 0])
        ax_volume = fig.add_subplot(gs[1, 0], sharex=ax_price)

        # Style axes
        for ax in [ax_price, ax_volume]:
            ax.set_facecolor(self.colors["bg"])
            ax.grid(True, linestyle="--", alpha=0.2, color=self.colors["grid"])
            for spine in ax.spines.values():
                spine.set_edgecolor(self.colors["text"])
                spine.set_linewidth(0.8)

        ax_price.set_ylabel("Price", fontweight="bold", color=self.colors["text"])
        ax_volume.set_ylabel("Volume", fontweight="bold", color=self.colors["text"])
        ax_volume.set_xlabel("Date", fontweight="bold", color=self.colors["text"])

        return fig, (ax_price, ax_volume)

    def _format_dates(self, ax: plt.Axes, df: pd.DataFrame, timeframe: str) -> None:
        """Format x-axis dates with sensible tick density."""
        n_bars = len(df)
        start_date = df.index[0]
        end_date = df.index[-1]
        date_range_days = (end_date - start_date).days

        # Increase max ticks to accommodate dense data
        mdates.MAXTICKS = 2000

        # Use AutoDateLocator for intelligent tick placement
        locator = mdates.AutoDateLocator(minticks=5, maxticks=20)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))

        # Add minor ticks
        ax.xaxis.set_minor_locator(mdates.AutoDateLocator(minticks=10, maxticks=30))

        # Rotate for readability
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    def _plot_candlesticks(self, ax: plt.Axes, df: pd.DataFrame) -> None:
        """Plot high-quality candlesticks with anti-aliased wicks."""
        n = len(df)
        x = np.arange(n)

        # Compute candle bodies
        bullish = df["close"].values >= df["open"].values
        bearish = df["close"].values < df["open"].values

        opens = df["open"].values
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values

        # Body heights
        body_height_bull = closes[bullish] - opens[bullish]
        body_height_bear = opens[bearish] - closes[bearish]
        body_bottom_bull = opens[bullish]
        body_bottom_bear = closes[bearish]

        # Width adaptive to number of bars
        bar_width = max(0.5, min(0.9, 1.0 / n * 50))

        # Plot bodies
        ax.bar(x[bullish], body_height_bull, bottom=body_bottom_bull,
               color=self.colors["price_up"], width=bar_width,
               edgecolor=self.colors["price_up"], linewidth=0.5, alpha=0.95,
               zorder=3)
        ax.bar(x[bearish], body_height_bear, bottom=body_bottom_bear,
               color=self.colors["price_down"], width=bar_width,
               edgecolor=self.colors["price_down"], linewidth=0.5, alpha=0.95,
               zorder=3)

        # Wicks (thin lines)
        ax.vlines(x[bullish], lows[bullish], highs[bullish],
                  color=self.colors["price_up"], linewidth=1, alpha=0.8, zorder=2)
        ax.vlines(x[bearish], lows[bearish], highs[bearish],
                  color=self.colors["price_down"], linewidth=1, alpha=0.8, zorder=2)

    def _plot_ema(self, ax: plt.Axes, df: pd.DataFrame) -> None:
        """Plot EMA with high-quality antialiasing."""
        ema_vals = self.indicator.ema.calculate(df["close"])
        ax.plot(np.arange(len(df)), ema_vals.values,
                color=self.colors["ema"], linewidth=3.0,
                linestyle="--", label="EMA 21", alpha=0.95, zorder=6,
                solid_capstyle="round", solid_joinstyle="round")

    def _plot_waves(self, ax: plt.Axes, waves: list[Wave], df: pd.DataFrame) -> None:
        """Plot Elliot Waves with clear markers and labels."""
        if not waves:
            return

        recent = waves[-4:]  # Show only last 4 waves for clarity
        for wave in recent:
            color = self.colors.get(f"wave{wave.wave_num}", "#ffffff")
            try:
                s = df.index.get_loc(wave.start_idx)
                e = df.index.get_loc(wave.end_idx)
            except KeyError:
                continue

            x_seg = np.arange(s, e + 1)
            y_seg = df["close"].iloc[s:e + 1].values

            # Wave line with rounded caps
            ax.plot(x_seg, y_seg, color=color, linewidth=4, marker="o",
                    markersize=8, markerfacecolor=color, markeredgecolor="white",
                    markeredgewidth=1.5, zorder=7, label=f"W{wave.wave_num}",
                    solid_capstyle="round", alpha=0.95)

            # Wave number label at start, offset to avoid overlap
            start_y = df["close"].iloc[s]
            offset = -20 if wave.direction == "down" else 20
            ax.annotate(
                f"W{wave.wave_num}",
                xy=(s, start_y), xytext=(0, offset),
                textcoords="offset points",
                fontsize=12, fontweight="bold", color=color,
                ha="center", va="center" if wave.direction == "down" else "bottom",
                arrowprops=dict(arrowstyle="-|>", color=color, alpha=0.7, linewidth=1.5),
                bbox=dict(boxstyle="round,pad=0.2", facecolor=self.colors["bg"],
                         edgecolor=color, alpha=0.9, linewidth=1)
            )

    def _plot_fibonacci(self, ax: plt.Axes, retracements: Dict[str, float],
                        extensions: Dict[str, float], n_bars: int) -> None:
        """Plot Fibonacci levels with clear right-side labels."""
        # Right side offset for labels
        label_x = n_bars + max(5, int(n_bars * 0.02))

        for i, (name, price) in enumerate(retracements.items()):
            y = price
            ax.axhline(y=y, color=self.colors["fib_ret"], linestyle=":",
                      linewidth=1.8, alpha=0.7, zorder=4)
            # Offset each label vertically to avoid overlap
            offset = -8 + i * 14
            ax.text(label_x, y, f" {name}", va="center", fontsize=10,
                   color=self.colors["fib_ret"], fontweight="bold", alpha=0.95,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors["bg"],
                            edgecolor=self.colors["fib_ret"], alpha=0.8, linewidth=0.5))

        for i, (name, price) in enumerate(extensions.items()):
            y = price
            ax.axhline(y=y, color=self.colors["fib_ext"], linestyle="-.",
                      linewidth=1.8, alpha=0.7, zorder=4)
            ax.text(label_x, y, f" {name}", va="center", fontsize=10,
                   color=self.colors["fib_ext"], fontweight="bold", alpha=0.95,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors["bg"],
                            edgecolor=self.colors["fib_ext"], alpha=0.8, linewidth=0.5))

    def _plot_signals_historical(self, ax: plt.Axes, signals_df: pd.DataFrame, df: pd.DataFrame) -> None:
        """Plot historical signal markers (last 5 only)."""
        if signals_df.empty:
            return

        for idx, row in signals_df.tail(5).iterrows():
            try:
                x_pos = df.index.get_loc(idx)
            except KeyError:
                continue

            price = row["price"]
            sig_type = row["signal"]
            conf = row.get("confidence", 0.5)
            color = self.colors["buy"] if sig_type == "BUY" else self.colors["sell"]
            marker = "^" if sig_type == "BUY" else "v"
            size = 140 if conf >= 0.8 else 110

            ax.scatter(x_pos, price, marker=marker, color=color, s=size,
                      zorder=12, edgecolors="black", linewidth=2.5, alpha=0.95,
                      clip_on=False)

            # Confidence label
            ax.annotate(f"{sig_type}\n{conf:.0%}",
                       xy=(x_pos, price),
                       xytext=(0, 22 if sig_type == "BUY" else -28),
                       textcoords="offset points",
                       ha="center", fontsize=10, fontweight="bold", color=color,
                       arrowprops=dict(arrowstyle="->", color=color, alpha=0.7, linewidth=2),
                       bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors["bg"],
                                edgecolor=color, alpha=0.9, linewidth=1))

    def _plot_latest_signal_details(self, ax: plt.Axes, signal: Optional[Signal],
                                     df: pd.DataFrame, n_bars: int) -> None:
        """Plot latest signal entry, TP, SL with prominent markers and labels."""
        if not signal:
            return

        entry_x = n_bars - 1
        entry_p = signal.price

        # ENTRY star (largest)
        ax.scatter(entry_x, entry_p, marker="*", color=self.colors["entry"],
                  s=400, zorder=20, edgecolors="black", linewidth=3,
                  clip_on=False)

        # Entry label
        ax.text(entry_x, entry_p * 1.008, f"ENTRY ${entry_p:,.0f}",
               ha="center", fontsize=13, fontweight="bold", color=self.colors["entry"],
               bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors["bg"],
                        edgecolor=self.colors["entry"], linewidth=2, alpha=0.95))

        # Stop Loss
        if signal.stop_loss:
            sl = signal.stop_loss
            ax.axhline(y=sl, color=self.colors["sl"], linestyle="--",
                      linewidth=3, alpha=0.85, zorder=8)
            ax.text(entry_x, sl * 0.992, f"SL ${sl:,.0f}",
                   ha="center", va="top", fontsize=11, fontweight="bold",
                   color=self.colors["sl"],
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors["bg"],
                            edgecolor=self.colors["sl"], linewidth=2, alpha=0.95))

        # Take Profit
        if signal.take_profit:
            tp = signal.take_profit
            ax.axhline(y=tp, color=self.colors["tp"], linestyle="--",
                      linewidth=3, alpha=0.85, zorder=8)
            ax.text(entry_x, tp * 1.008, f"TP ${tp:,.0f}",
                   ha="center", va="bottom", fontsize=11, fontweight="bold",
                   color=self.colors["tp"],
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors["bg"],
                            edgecolor=self.colors["tp"], linewidth=2, alpha=0.95))

    def _plot_volume(self, ax: plt.Axes, df: pd.DataFrame) -> None:
        """Plot colored volume bars."""
        if "volume" not in df.columns or df["volume"].isna().all():
            ax.set_visible(False)
            return

        x = np.arange(len(df))
        colors = [self.colors["volume_up"] if c >= o else self.colors["volume_down"]
                 for c, o in zip(df["close"].values, df["open"].values)]

        ax.bar(x, df["volume"].values, color=colors, width=0.7,
               alpha=0.85, edgecolor="none", zorder=3)
        ax.set_ylabel("Volume", fontweight="bold", color=self.colors["text"])
        ax.tick_params(axis='y', labelsize=9)
        ax.yaxis.set_tick_params(labelleft=True)

    def _plot_support_resistance(self, ax: plt.Axes, levels: Dict[str, List[float]]) -> None:
        """Plot support/resistance levels."""
        for level in levels.get("support", []):
            ax.axhline(y=level, color=self.colors["support"], linestyle=":",
                      linewidth=1.5, alpha=0.5, zorder=3)
        for level in levels.get("resistance", []):
            ax.axhline(y=level, color=self.colors["resistance"], linestyle=":",
                      linewidth=1.5, alpha=0.5, zorder=3)

    def _add_title(self, ax: plt.Axes, symbol: str, timeframe: str, latest_signal: Optional[Signal]) -> None:
        """Add informative title."""
        title = f"{symbol} — {timeframe.upper()} Elliot Wave Analysis"
        if latest_signal:
            title += f" | {latest_signal.signal_type} @ ${latest_signal.price:,.0f} ({latest_signal.confidence:.0%})"
        ax.set_title(title, fontsize=15, fontweight="bold", pad=18,
                    color=self.colors["text"], loc="left")

    def _add_legend(self, ax: plt.Axes, latest_signal: Optional[Signal]) -> None:
        """Add compact, informative legend."""
        items = [
            plt.Line2D([0], [0], color=self.colors["ema"], linestyle="--",
                      label="EMA 21", linewidth=2.5),
            plt.Rectangle((0,0),1,1, facecolor=self.colors["price_up"],
                         label="Bullish", alpha=0.9),
            plt.Rectangle((0,0),1,1, facecolor=self.colors["price_down"],
                         label="Bearish", alpha=0.9),
        ]

        if latest_signal:
            col = self.colors["buy"] if latest_signal.signal_type == "BUY" else self.colors["sell"]
            mark = "^" if latest_signal.signal_type == "BUY" else "v"
            items.append(plt.Line2D([0], [0], marker=mark, color=col,
                                   label=f"{latest_signal.signal_type} Signal",
                                   linestyle="None", markersize=10,
                                   markeredgecolor="black", markeredgewidth=1))

        ax.legend(handles=items, loc="upper left", fontsize=10,
                 framealpha=0.95, ncol=3, frameon=True, fancybox=True,
                 shadow=True, borderpad=0.6)

    def _add_info_box(self, ax: plt.Axes, signal: Optional[Signal]) -> None:
        """Add signal details info box."""
        if not signal:
            return

        lines = [
            f"Signal : {signal.signal_type}",
            f"Wave   : {signal.wave_num}",
            f"Entry  : ${signal.price:,.0f}",
        ]
        lines.append(f"SL     : ${signal.stop_loss:,.0f}" if signal.stop_loss else "SL     : N/A")
        lines.append(f"TP     : ${signal.take_profit:,.0f}" if signal.take_profit else "TP     : N/A")
        lines.append(f"Conf   : {signal.confidence:.0%}")

        text = "\n".join(lines)

        props = dict(
            boxstyle="round,pad=0.8",
            facecolor=self.colors["bg"],
            alpha=0.95,
            edgecolor=self.colors["sl"] if signal.signal_type == "SELL" else self.colors["tp"],
            linewidth=2
        )

        ax.text(0.995, 0.95, text, transform=ax.transAxes,
                fontsize=11, fontweight="bold", family="monospace",
                verticalalignment="top", horizontalalignment="right",
                bbox=props)

    def plot(
        self,
        df: pd.DataFrame,
        output_path: str,
        symbol: str = "BTC/USDT",
        timeframe: str = "4h",
        format: Literal["png", "pdf", "svg", "eps"] = "png",
        dpi: Optional[int] = None,
        show_plot: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate and save high-resolution chart.

        Args:
            df: OHLCV DataFrame.
            output_path: Output file path (extension determines format).
            symbol: Trading pair name.
            timeframe: Timeframe string (affects date format and layout).
            format: Output format — 'png', 'pdf', 'svg', or 'eps'.
            dpi: Override DPI (default uses self.base_dpi; vector formats ignore).
            show_plot: If True, display interactive window.
            metadata: Optional dict of metadata to embed (for PNG/PDF).

        Returns:
            Absolute path to saved file.
        """
        # Analysis
        results = self.indicator.analyze(df)
        waves = results["waves"]
        retracements = results.get("retracements", {})
        extensions = results.get("extensions", {})
        latest_signal = self.indicator.get_latest_signal(df)
        support_resistance = self.indicator.get_support_resistance(df, lookback=60)

        # Figure setup
        n_bars = len(df)
        fig, (ax_price, ax_volume) = self._create_figure(n_bars, timeframe)

        # --- Price panel ---
        self._plot_candlesticks(ax_price, df)
        self._plot_ema(ax_price, df)
        self._plot_waves(ax_price, waves, df)
        self._plot_fibonacci(ax_price, retracements, extensions, n_bars)
        self._plot_signals_historical(ax_price, results["signals"], df)
        self._plot_latest_signal_details(ax_price, latest_signal, df, n_bars)
        self._plot_support_resistance(ax_price, support_resistance)
        self._format_dates(ax_price, df, timeframe)
        self._add_title(ax_price, symbol, timeframe, latest_signal)
        self._add_legend(ax_price, latest_signal)
        self._add_info_box(ax_price, latest_signal)

        ax_price.set_ylabel("Price (USDT)", fontweight="bold", color=self.colors["text"])

        # --- Volume panel ---
        self._plot_volume(ax_volume, df)
        ax_volume.set_xlabel("Date", fontweight="bold", color=self.colors["text"])

        # Save
        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)

        save_kwargs = {
            "dpi": dpi or self.base_dpi,
            "facecolor": fig.get_facecolor(),
            "edgecolor": "none",
            "bbox_inches": "tight",
            "pad_inches": 0.3,
        }

        # Auto-generate metadata if not provided
        if metadata is None:
            metadata = {
                "Title": f"{symbol} Elliot Wave Analysis — {timeframe.upper()}",
                "Author": "CryptoElliotWaveIndicator",
                "CreationDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Producer": "Matplotlib",
                "Subject": f"Wave count: {len(waves)} | Latest: {latest_signal.signal_type if latest_signal else 'N/A'}",
            }
        save_kwargs["metadata"] = metadata

        # Choose backend based on format
        if format == "png":
            # PNG with optimal compression
            save_kwargs["format"] = "png"
            save_kwargs["transparent"] = False
        elif format == "pdf":
            save_kwargs["format"] = "pdf"
        elif format == "svg":
            save_kwargs["format"] = "svg"
        elif format == "eps":
            save_kwargs["format"] = "eps"

        fig.savefig(output_path, **save_kwargs)

        if show_plot:
            plt.show()
        plt.close(fig)

        return os.path.abspath(output_path)


# Convenience function
def generate_chart(
    df: pd.DataFrame,
    indicator: CryptoElliotWaveIndicator,
    output_path: str,
    symbol: str = "BTC/USDT",
    timeframe: str = "4h",
    theme: Literal["light", "dark"] = "light",
    dpi: int = 300,
    format: Literal["png", "pdf", "svg", "eps"] = "png",
    **kwargs
) -> str:
    """
    Generate a high-resolution professional chart.

    Args:
        df: OHLCV data.
        indicator: Initialized CryptoElliotWaveIndicator.
        output_path: Output file path.
        symbol: Trading pair (e.g., "BTC/USDT").
        timeframe: "4h", "1d", etc.
        theme: "light" or "dark" background.
        dpi: Resolution (min 150, max 1200, default 300).
        format: Output format — png (default), pdf (vector), svg (vector), eps (vector).
        **kwargs: Additional args passed to HighResolutionPlotter.plot().

    Returns:
        Absolute path to saved file.

    Example:
        indicator = CryptoElliotWaveIndicator()
        df = fetch_ohlcv("binance", "BTC/USDT", "1d", 500)
        path = generate_chart(df, indicator, "charts/daily.pdf",
                            symbol="BTC/USDT", timeframe="1d", dpi=600, format="pdf")
    """
    plotter = HighResolutionPlotter(indicator, theme=theme, base_dpi=dpi)
    return plotter.plot(df=df, output_path=output_path, symbol=symbol,
                       timeframe=timeframe, format=format, **kwargs)
