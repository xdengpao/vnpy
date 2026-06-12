from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib import import_module
from pathlib import Path
from time import sleep
from typing import Any

import numpy as np

from vnpy.alpha.lab import AlphaLab
from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange
from vnpy.trader.constant import Interval
from vnpy.trader.datafeed import get_datafeed
import vnpy.trader.datafeed as datafeed_module
from vnpy.trader.database import get_database
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.setting import SETTINGS
from vnpy.trader.utility import extract_vt_symbol

from .config import VnpymConfig, parse_date


@dataclass(frozen=True)
class CryptoGatewaySpec:
    """Built-in cryptocurrency history gateway metadata."""

    name: str
    module: str
    class_name: str
    exchange: Exchange
    rest_host_attr: str
    testnet_rest_host_attr: str = ""
    usdt_rest_host_attr: str = ""
    coin_rest_host_attr: str = ""
    usdt_testnet_rest_host_attr: str = ""
    coin_testnet_rest_host_attr: str = ""
    description: str = ""


CRYPTO_GATEWAYS: dict[str, CryptoGatewaySpec] = {
    "binance_spot": CryptoGatewaySpec(
        name="binance_spot",
        module="vnpy.gateway.binance.binance_gateway",
        class_name="BinanceGateway",
        exchange=Exchange.BINANCE,
        rest_host_attr="REST_HOST",
        description="Binance spot public kline API",
    ),
    "binance_usdt_futures": CryptoGatewaySpec(
        name="binance_usdt_futures",
        module="vnpy.gateway.binances.binances_gateway",
        class_name="BinancesGateway",
        exchange=Exchange.BINANCE,
        rest_host_attr="F_REST_HOST",
        usdt_rest_host_attr="F_REST_HOST",
        coin_rest_host_attr="D_REST_HOST",
        usdt_testnet_rest_host_attr="F_TESTNET_RESTT_HOST",
        coin_testnet_rest_host_attr="D_TESTNET_RESTT_HOST",
        description="Binance USDT-margined futures public kline API",
    ),
    "binance_coin_futures": CryptoGatewaySpec(
        name="binance_coin_futures",
        module="vnpy.gateway.binances.binances_gateway",
        class_name="BinancesGateway",
        exchange=Exchange.BINANCE,
        rest_host_attr="D_REST_HOST",
        usdt_rest_host_attr="F_REST_HOST",
        coin_rest_host_attr="D_REST_HOST",
        usdt_testnet_rest_host_attr="F_TESTNET_RESTT_HOST",
        coin_testnet_rest_host_attr="D_TESTNET_RESTT_HOST",
        description="Binance coin-margined futures public kline API",
    ),
    "huobi_spot": CryptoGatewaySpec(
        name="huobi_spot",
        module="vnpy.gateway.huobi.huobi_gateway",
        class_name="HuobiGateway",
        exchange=Exchange.HUOBI,
        rest_host_attr="REST_HOST",
        description="Huobi spot public kline API",
    ),
    "gateio_futures": CryptoGatewaySpec(
        name="gateio_futures",
        module="vnpy.gateway.gateios.gateios_gateway",
        class_name="GateiosGateway",
        exchange=Exchange.GATEIO,
        rest_host_attr="REST_HOST",
        testnet_rest_host_attr="TESTNET_REST_HOST",
        description="Gate.io futures public kline API",
    ),
    "bitmex": CryptoGatewaySpec(
        name="bitmex",
        module="vnpy.gateway.bitmex.bitmex_gateway",
        class_name="BitmexGateway",
        exchange=Exchange.BITMEX,
        rest_host_attr="REST_HOST",
        testnet_rest_host_attr="TESTNET_REST_HOST",
        description="BitMEX public kline API",
    ),
    "bitfinex": CryptoGatewaySpec(
        name="bitfinex",
        module="vnpy.gateway.bitfinex.bitfinex_gateway",
        class_name="BitfinexGateway",
        exchange=Exchange.BITFINEX,
        rest_host_attr="REST_HOST",
        description="Bitfinex public kline API",
    ),
    "bitstamp": CryptoGatewaySpec(
        name="bitstamp",
        module="vnpy.gateway.bitstamp.bitstamp_gateway",
        class_name="BitstampGateway",
        exchange=Exchange.BITSTAMP,
        rest_host_attr="REST_HOST",
        description="Bitstamp public kline API",
    ),
    "coinbase": CryptoGatewaySpec(
        name="coinbase",
        module="vnpy.gateway.coinbase.coinbase_gateway",
        class_name="CoinbaseGateway",
        exchange=Exchange.COINBASE,
        rest_host_attr="REST_HOST",
        testnet_rest_host_attr="SANDBOX_REST_HOST",
        description="Coinbase public kline API",
    ),
}


@dataclass
class SyncResult:
    """Historical data synchronization result."""

    counts: dict[str, int]

    @property
    def total(self) -> int:
        """Return total number of synchronized bars."""
        return sum(self.counts.values())


class MarketDataService:
    """Fetch, import, and persist market data for the integrated workflow."""

    def __init__(self, config: VnpymConfig) -> None:
        self.config: VnpymConfig = config
        self.lab: AlphaLab = AlphaLab(config.lab_path)

    def sync_history(self) -> SyncResult:
        """Fetch historical bars from the configured source."""
        if self.config.datafeed.source == "crypto_gateway":
            return self.sync_crypto_history()

        return self.sync_datafeed_history()

    def sync_datafeed_history(self) -> SyncResult:
        """Fetch historical bars from configured vn.py datafeed."""
        self._apply_datafeed_settings()

        datafeed = get_datafeed()
        if not datafeed.init():
            raise RuntimeError("datafeed initialization failed")

        interval: Interval = Interval(self.config.interval)
        start: datetime = parse_date(self.config.start)
        end: datetime = parse_date(self.config.end)
        counts: dict[str, int] = {}

        database = get_database() if self.config.datafeed.save_to_database else None

        for vt_symbol in self.config.symbols:
            symbol, exchange = extract_vt_symbol(vt_symbol)
            req = HistoryRequest(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start=start,
                end=end,
            )
            bars = datafeed.query_bar_history(req) or []
            self.lab.save_bar_data(bars)

            if database and bars:
                database.save_bar_data(bars)

            counts[vt_symbol] = len(bars)

        return SyncResult(counts)

    def sync_crypto_history(self, gateway_name: str | None = None) -> SyncResult:
        """Fetch historical bars from a selected cryptocurrency gateway."""
        selected_gateway = gateway_name or self.config.crypto_gateway.name
        spec = get_crypto_gateway_spec(selected_gateway)
        gateway = create_crypto_gateway(spec, self.config)

        interval: Interval = Interval(self.config.interval)
        start: datetime = parse_date(self.config.start)
        end: datetime = parse_date(self.config.end)
        counts: dict[str, int] = {}
        database = get_database() if self.config.datafeed.save_to_database else None

        try:
            for vt_symbol in self.config.symbols:
                symbol, exchange = extract_vt_symbol(vt_symbol)
                if exchange != spec.exchange:
                    raise ValueError(
                        f"{vt_symbol} exchange must be {spec.exchange.value} "
                        f"when crypto_gateway.name is {spec.name}"
                    )

                req = HistoryRequest(
                    symbol=symbol,
                    exchange=exchange,
                    interval=interval,
                    start=start,
                    end=end,
                )
                try:
                    bars = gateway.query_history(req) or []
                except Exception as exc:
                    rest_host = getattr(gateway.rest_api, "url_base", "")
                    proxy = gateway.rest_api.proxies or {}
                    raise RuntimeError(
                        "crypto history download failed: "
                        f"gateway={spec.name}, symbol={vt_symbol}, "
                        f"rest_host={rest_host}, proxy={proxy}"
                    ) from exc

                self.lab.save_bar_data(bars)

                if database and bars:
                    database.save_bar_data(bars)

                counts[vt_symbol] = len(bars)
        finally:
            gateway.close()

        return SyncResult(counts)

    def generate_sample_data(self, days: int | None = None) -> SyncResult:
        """Generate deterministic local sample bars for development runs."""
        interval: Interval = Interval(self.config.interval)

        start: datetime = parse_date(self.config.start)
        end: datetime = parse_date(self.config.end)
        if days:
            end = min(end, start + timedelta(days=days - 1))

        counts: dict[str, int] = {}
        rng = np.random.default_rng(seed=42)

        for index, vt_symbol in enumerate(self.config.symbols):
            symbol, exchange = extract_vt_symbol(vt_symbol)
            price: float = float(10 + index * 5)
            bars: list[BarData] = []
            current = start

            while current <= end:
                drift = 0.0003 + index * 0.0001
                shock = float(rng.normal(0, 0.015))
                open_price = price
                close_price = max(1, price * (1 + drift + shock))
                high_price = max(open_price, close_price) * (1 + abs(float(rng.normal(0, 0.005))))
                low_price = min(open_price, close_price) * (1 - abs(float(rng.normal(0, 0.005))))
                volume = float(100_000 + rng.integers(1_000, 20_000))
                turnover = close_price * volume

                bars.append(
                    BarData(
                        symbol=symbol,
                        exchange=exchange,
                        datetime=current,
                        interval=interval,
                        volume=volume,
                        turnover=turnover,
                        open_interest=0,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        gateway_name="VNpymSample",
                    )
                )
                price = close_price

                current += get_interval_delta(interval)

            self.lab.save_bar_data(bars)
            counts[vt_symbol] = len(bars)

        return SyncResult(counts)

    def import_csv(self, path: str | Path, vt_symbol: str) -> int:
        """Import OHLCV bars from a CSV file into the local AlphaLab."""
        import pandas as pd

        symbol, exchange = extract_vt_symbol(vt_symbol)
        interval: Interval = Interval(self.config.interval)
        df = pd.read_csv(path)
        bars: list[BarData] = []

        for row in df.to_dict("records"):
            dt = datetime.fromisoformat(str(row["datetime"]))
            volume = float(row.get("volume", 0))
            close_price = float(row["close"])
            turnover = float(row.get("turnover", close_price * volume))
            bars.append(
                BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    interval=interval,
                    volume=volume,
                    turnover=turnover,
                    open_interest=float(row.get("open_interest", 0)),
                    open_price=float(row["open"]),
                    high_price=float(row["high"]),
                    low_price=float(row["low"]),
                    close_price=close_price,
                    gateway_name="CSV",
                )
            )

        self.lab.save_bar_data(bars)
        return len(bars)

    def _apply_datafeed_settings(self) -> None:
        """Apply config to vn.py global datafeed settings."""
        SETTINGS["datafeed.name"] = self.config.datafeed.name
        SETTINGS["datafeed.username"] = self.config.datafeed.username
        SETTINGS["datafeed.password"] = self.config.datafeed.password
        datafeed_module.datafeed = None


def get_interval_delta(interval: Interval) -> timedelta:
    """Return timedelta for supported bar intervals."""
    if interval == Interval.MINUTE:
        return timedelta(minutes=1)
    if interval == Interval.HOUR:
        return timedelta(hours=1)
    if interval == Interval.DAILY:
        return timedelta(days=1)

    raise ValueError(f"unsupported sample interval: {interval.value}")


def available_crypto_gateways() -> dict[str, str]:
    """Return built-in cryptocurrency gateway choices."""
    return {name: spec.description for name, spec in CRYPTO_GATEWAYS.items()}


def get_crypto_gateway_spec(name: str) -> CryptoGatewaySpec:
    """Return metadata for a configured cryptocurrency gateway."""
    try:
        return CRYPTO_GATEWAYS[name]
    except KeyError as exc:
        available = ", ".join(sorted(CRYPTO_GATEWAYS))
        raise ValueError(f"unknown crypto gateway {name!r}; available: {available}") from exc


def create_crypto_gateway(spec: CryptoGatewaySpec, config: VnpymConfig) -> Any:
    """Create a gateway instance initialized for synchronous public history queries."""
    module = import_module(spec.module)
    gateway_class = getattr(module, spec.class_name)
    gateway = gateway_class(EventEngine())

    rest_host = resolve_rest_host(module, spec, config)
    rest_api = gateway.rest_api
    rest_api.init(
        rest_host,
        config.crypto_gateway.proxy_host,
        config.crypto_gateway.proxy_port,
    )
    if not config.crypto_gateway.proxy_host and not config.crypto_gateway.use_env_proxy:
        rest_api.proxies = {"http": None, "https": None}
    install_request_retry(rest_api, config)

    # Some legacy crypto REST APIs read these attributes inside query_history.
    if spec.class_name == "BinancesGateway":
        rest_api.usdt_base = config.crypto_gateway.usdt_base
        rest_api.server = config.crypto_gateway.server
        if spec.name == "binance_coin_futures":
            rest_api.usdt_base = False

    return gateway


def install_request_retry(rest_api: Any, config: VnpymConfig) -> None:
    """Install lightweight retry around legacy synchronous REST requests."""
    if not hasattr(rest_api, "request"):
        return

    original_request = rest_api.request
    retries = max(1, config.crypto_gateway.request_retries)
    retry_delay = max(0, config.crypto_gateway.retry_delay)

    def request_with_retry(*args: Any, **kwargs: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                return original_request(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                if attempt + 1 < retries and retry_delay:
                    sleep(retry_delay)

        if last_error:
            raise last_error

        return original_request(*args, **kwargs)

    rest_api.request = request_with_retry


def resolve_rest_host(module: Any, spec: CryptoGatewaySpec, config: VnpymConfig) -> str:
    """Resolve REST host constant for a built-in crypto gateway."""
    if config.crypto_gateway.rest_host:
        return config.crypto_gateway.rest_host

    server = config.crypto_gateway.server.upper()

    if spec.class_name == "BinancesGateway":
        usdt_base = config.crypto_gateway.usdt_base
        if spec.name == "binance_coin_futures":
            usdt_base = False

        if server == "TESTNET":
            attr = spec.usdt_testnet_rest_host_attr if usdt_base else spec.coin_testnet_rest_host_attr
        else:
            attr = spec.usdt_rest_host_attr if usdt_base else spec.coin_rest_host_attr

        return str(getattr(module, attr))

    if server == "TESTNET" and spec.testnet_rest_host_attr:
        return str(getattr(module, spec.testnet_rest_host_attr))

    return str(getattr(module, spec.rest_host_attr))
