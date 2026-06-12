from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from vnpy.trader.constant import Interval
from vnpy.trader.utility import extract_vt_symbol


DATE_FORMAT = "%Y-%m-%d"


@dataclass
class DatafeedConfig:
    """External historical datafeed settings."""

    source: str = "datafeed"
    name: str = ""
    username: str = ""
    password: str = ""
    save_to_database: bool = True


@dataclass
class CryptoGatewayConfig:
    """Cryptocurrency gateway history download settings."""

    name: str = "binance_spot"
    server: str = "REAL"
    usdt_base: bool = True
    rest_host: str = ""
    proxy_host: str = ""
    proxy_port: int = 0
    use_env_proxy: bool = False
    request_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class TrainingConfig:
    """Model training settings."""

    model_name: str = "vnpym_model"
    signal_name: str = "vnpym_signal"
    feature_window: int = 20
    label_horizon: int = 5
    valid_ratio: float = 0.2
    ridge_alpha: float = 1.0


@dataclass
class ExecutionConfig:
    """Trading execution settings."""

    mode: str = "paper"
    capital: float = 1_000_000
    cash_ratio: float = 0.95
    top_k: int = 3
    long_only: bool = True
    min_volume: float = 100
    price_add: float = 0
    output_path: str = "lab/vnpym/execution"
    allow_live_trading: bool = False
    gateway_module: str = ""
    gateway_class: str = ""
    gateway_name: str = ""
    gateway_setting: dict[str, Any] = field(default_factory=dict)


@dataclass
class VnpymConfig:
    """Unified vnpym project configuration."""

    lab_path: str = "lab/vnpym"
    symbols: list[str] = field(default_factory=lambda: ["000001.SZSE", "600000.SSE"])
    interval: str = Interval.DAILY.value
    start: str = "2023-01-01"
    end: str = "2024-12-31"
    datafeed: DatafeedConfig = field(default_factory=DatafeedConfig)
    crypto_gateway: CryptoGatewayConfig = field(default_factory=CryptoGatewayConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)

    def validate(self) -> None:
        """Validate config values before running the workflow."""
        if not self.symbols:
            raise ValueError("symbols must not be empty")

        for vt_symbol in self.symbols:
            extract_vt_symbol(vt_symbol)

        Interval(self.interval)
        parse_date(self.start)
        parse_date(self.end)

        if parse_date(self.start) >= parse_date(self.end):
            raise ValueError("start must be earlier than end")

        if self.datafeed.source not in {"datafeed", "crypto_gateway"}:
            raise ValueError("datafeed.source must be 'datafeed' or 'crypto_gateway'")

        if self.training.feature_window < 2:
            raise ValueError("training.feature_window must be >= 2")

        if self.training.label_horizon < 1:
            raise ValueError("training.label_horizon must be >= 1")

        if not 0 < self.training.valid_ratio < 1:
            raise ValueError("training.valid_ratio must be between 0 and 1")

        if self.execution.mode not in {"paper", "live"}:
            raise ValueError("execution.mode must be either 'paper' or 'live'")

        if self.execution.top_k < 1:
            raise ValueError("execution.top_k must be >= 1")

        if self.execution.min_volume <= 0:
            raise ValueError("execution.min_volume must be > 0")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VnpymConfig:
        """Build config from a JSON-compatible dictionary."""
        data = dict(data)
        datafeed = DatafeedConfig(**data.pop("datafeed", {}))
        crypto_gateway = CryptoGatewayConfig(**data.pop("crypto_gateway", {}))
        training = TrainingConfig(**data.pop("training", {}))
        execution = ExecutionConfig(**data.pop("execution", {}))
        return cls(
            **data,
            datafeed=datafeed,
            crypto_gateway=crypto_gateway,
            training=training,
            execution=execution,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to a JSON-compatible dictionary."""
        return asdict(self)


def parse_date(value: str) -> datetime:
    """Parse a YYYY-MM-DD date string."""
    return datetime.strptime(value, DATE_FORMAT)


def create_default_config(path: str | Path | None = None) -> VnpymConfig:
    """Create a default project config."""
    config = VnpymConfig()
    if path:
        save_config(config, path)
    return config


def load_config(path: str | Path) -> VnpymConfig:
    """Load project config from JSON."""
    config_path = Path(path)
    with open(config_path, encoding="UTF-8") as f:
        data: dict[str, Any] = json.load(f)

    config = VnpymConfig.from_dict(data)
    config.validate()
    return config


def save_config(config: VnpymConfig, path: str | Path) -> None:
    """Save project config to JSON."""
    config.validate()
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, mode="w", encoding="UTF-8") as f:
        json.dump(config.to_dict(), f, indent=4, ensure_ascii=False)
