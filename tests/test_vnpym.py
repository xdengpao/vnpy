from pathlib import Path
from types import ModuleType
import sys

from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.constant import Interval
from vnpy.vnpym import VnpymPipeline
from vnpy.vnpym.config import VnpymConfig
import vnpy.vnpym.data as data_module
from vnpy.vnpym.data import CryptoGatewaySpec, MarketDataService, available_crypto_gateways


def make_config(tmp_path: Path) -> VnpymConfig:
    """Create a compact test config."""
    config = VnpymConfig(
        lab_path=str(tmp_path.joinpath("lab")),
        symbols=["000001.SZSE", "600000.SSE", "000333.SZSE"],
        start="2023-01-01",
        end="2023-06-30",
    )
    config.execution.output_path = str(tmp_path.joinpath("execution"))
    config.execution.top_k = 2
    return config


def test_sample_train_and_paper_trade(tmp_path: Path) -> None:
    """Run the integrated workflow using deterministic sample data."""
    config = make_config(tmp_path)

    result = VnpymPipeline(config).run(sample=True)

    assert result.sync
    assert result.sync.total > 0
    assert result.training
    assert result.training.rows > 0
    assert result.training.model_path.exists()
    assert result.training.signal_path.exists()
    assert result.execution
    assert result.execution.order_path.exists()
    assert result.execution.position_path.exists()


def test_run_without_trade(tmp_path: Path) -> None:
    """Allow training-only runs for research workflows."""
    config = make_config(tmp_path)

    result = VnpymPipeline(config).run(sample=True, trade=False)

    assert result.sync
    assert result.training
    assert result.execution is None


def test_available_crypto_gateways() -> None:
    """Expose selectable crypto gateway choices."""
    gateways = available_crypto_gateways()

    assert "binance_spot" in gateways
    assert "binance_usdt_futures" in gateways


def test_sync_crypto_history_with_selected_gateway(tmp_path: Path, monkeypatch) -> None:
    """Route history download through the selected crypto gateway."""
    module = ModuleType("tests.fake_crypto_gateway")
    module.REST_HOST = "https://example.test"

    class FakeRestApi:
        def __init__(self) -> None:
            self.inited = False

        def init(self, rest_host: str, proxy_host: str = "", proxy_port: int = 0) -> None:
            self.inited = True

    class FakeGateway:
        def __init__(self, event_engine) -> None:
            self.gateway_name = "FAKE"
            self.rest_api = FakeRestApi()
            self.closed = False

        def query_history(self, req: HistoryRequest) -> list[BarData]:
            assert self.rest_api.inited
            return [
                BarData(
                    symbol=req.symbol,
                    exchange=req.exchange,
                    datetime=req.start,
                    interval=req.interval or Interval.DAILY,
                    open_price=1,
                    high_price=2,
                    low_price=0.5,
                    close_price=1.5,
                    volume=100,
                    turnover=150,
                    gateway_name=self.gateway_name,
                )
            ]

        def write_log(self, msg: str) -> None:
            pass

        def close(self) -> None:
            self.closed = True

    module.FakeGateway = FakeGateway
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setitem(
        data_module.CRYPTO_GATEWAYS,
        "fake_crypto",
        CryptoGatewaySpec(
            name="fake_crypto",
            module=module.__name__,
            class_name="FakeGateway",
            exchange=data_module.Exchange.BINANCE,
            rest_host_attr="REST_HOST",
            description="Fake crypto gateway",
        ),
    )

    config = VnpymConfig(
        lab_path=str(tmp_path.joinpath("lab")),
        symbols=["BTCUSDT.BINANCE"],
        interval="d",
        start="2024-01-01",
        end="2024-01-02",
    )
    config.datafeed.source = "crypto_gateway"
    config.crypto_gateway.name = "fake_crypto"
    config.datafeed.save_to_database = False

    result = MarketDataService(config).sync_history()

    assert result.total == 1
