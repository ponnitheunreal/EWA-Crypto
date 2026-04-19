# exchange.py — Live Market Data Fetcher using CCXT

import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime

# Note: ccxt is an optional dependency. Install with:
#   pip install ccxt
# Import is done lazily in methods to avoid hard requirement at module import time.


class ExchangeFetcher:
    """
    Fetches OHLCV data from cryptocurrency exchanges via CCXT.

    Supported exchanges: Binance, Coinbase, Kraken, KuCoin, OKX, Bybit, and 100+ more.

    Example:
        fetcher = ExchangeFetcher("binance")
        df = fetcher.fetch_ohlcv(symbol="BTC/USDT", timeframe="4h", limit=500)
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize exchange connection.

        Args:
            exchange_id: CCXT exchange ID (e.g., "binance", "coinbase", "kraken")
            api_key: Optional API key for private endpoints (not needed for public OHLCV)
            secret: Optional secret key
            **kwargs: Additional exchange-specific options (rateLimit, timeout, etc.)
        """
        try:
            import ccxt  # type: ignore
        except ImportError as e:
            raise ImportError(
                "CCXT is required for live data fetching. "
                "Install it with: pip install ccxt"
            ) from e

        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': secret,
            **kwargs
        })

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "4h",
        limit: int = 500,
        since: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV candlestick data from the exchange.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT", "ETH/USD")
            timeframe: Candle interval ("1m", "5m", "15m", "1h", "4h", "1d", etc.)
            limit: Number of candles to fetch (max varies by exchange, typically 1000)
            since: Optional timestamp in milliseconds to start from
            params: Additional exchange-specific parameters

        Returns:
            pandas DataFrame with columns: open, high, low, close, volume
            Index: datetime (timezone-aware if exchange provides it)

        Raises:
            ccxt.BaseError: On network/exchange errors
        """
        # Fetch raw OHLCV from exchange
        raw = self.exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            since=since,
            params=params or {}
        )

        # Convert to DataFrame
        # CCXT returns: [[timestamp, open, high, low, close, volume], ...]
        df = pd.DataFrame(
            raw,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)

        # Ensure numeric types
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])

        return df

    def fetch_ticker(
        self,
        symbol: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch current ticker data (last price, bid, ask, etc.).

        Args:
            symbol: Trading pair
            params: Additional exchange-specific parameters

        Returns:
            Dictionary with ticker information
        """
        return self.exchange.fetch_ticker(symbol, params=params or {})

    def fetch_order_book(
        self,
        symbol: str,
        limit: int = 20,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch current order book.

        Args:
            symbol: Trading pair
            limit: Number of bids/asks to fetch
            params: Additional exchange-specific parameters

        Returns:
            Order book dictionary with 'bids' and 'asks'
        """
        return self.exchange.fetch_order_book(symbol, limit=limit, params=params or {})

    def get_supported_timeframes(self, symbol: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get supported timeframes for this exchange.

        Returns:
            Dictionary mapping exchange name to list of timeframe strings.
        """
        if symbol:
            return self.exchange.fetch_timeframes(symbol)
        return self.exchange.timeframes

    def close(self) -> None:
        """Close exchange connection (no-op for most CCXT exchanges)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions for one-liner usage

def fetch_ohlcv(
    exchange_id: str = "binance",
    symbol: str = "BTC/USDT",
    timeframe: str = "4h",
    limit: int = 500,
    **kwargs
) -> pd.DataFrame:
    """
    One-liner to fetch OHLCV data from an exchange.

    Example:
        df = fetch_ohlcv("binance", "BTC/USDT", "4h", 500)
    """
    fetcher = ExchangeFetcher(exchange_id)
    return fetcher.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit, **kwargs)


def fetch_current_price(
    exchange_id: str = "binance",
    symbol: str = "BTC/USDT"
) -> float:
    """
    One-liner to fetch current last price.

    Example:
        price = fetch_current_price("binance", "BTC/USDT")
    """
    fetcher = ExchangeFetcher(exchange_id)
    ticker = fetcher.fetch_ticker(symbol)
    return ticker["last"]
