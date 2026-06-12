from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any

import polars as pl

from vnpy.alpha.lab import AlphaLab
from vnpy.event import EventEngine
from vnpy.trader.constant import Direction, Interval, Offset, OrderType
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import OrderRequest
from vnpy.trader.utility import extract_vt_symbol, floor_to

from .config import VnpymConfig, parse_date


@dataclass
class PlannedOrder:
    """Order plan generated from latest model signals."""

    datetime: str
    vt_symbol: str
    direction: str
    offset: str
    price: float
    volume: float
    signal: float
    mode: str
    vt_orderid: str = ""


@dataclass
class ExecutionResult:
    """Execution result with output paths."""

    orders: list[PlannedOrder]
    order_path: Path
    position_path: Path


class ExecutionService:
    """Convert signals into paper or explicitly enabled live execution."""

    def __init__(self, config: VnpymConfig) -> None:
        self.config: VnpymConfig = config
        self.lab: AlphaLab = AlphaLab(config.lab_path)

    def execute(self) -> ExecutionResult:
        """Execute latest saved signal according to configured mode."""
        signal_df = self.lab.load_signal(self.config.training.signal_name)
        if signal_df is None or signal_df.is_empty():
            raise RuntimeError("signal file is missing or empty; run train first")

        planned_orders = self.plan_orders(signal_df)
        if self.config.execution.mode == "live":
            self._execute_live(planned_orders)

        return self._persist_paper_result(planned_orders)

    def plan_orders(self, signal_df: pl.DataFrame) -> list[PlannedOrder]:
        """Create target orders from latest signal date."""
        latest_dt = signal_df["datetime"].max()
        latest_signal = (
            signal_df
            .filter(pl.col("datetime") == latest_dt)
            .sort("signal", descending=True)
            .head(self.config.execution.top_k)
        )

        if latest_signal.is_empty():
            return []

        positions = self._load_positions()
        prices = self._load_latest_prices()
        selected = latest_signal.to_dicts()
        target_value = self.config.execution.capital * self.config.execution.cash_ratio / len(selected)
        orders: list[PlannedOrder] = []

        for row in selected:
            vt_symbol = str(row["vt_symbol"])
            signal = float(row["signal"])
            price = prices.get(vt_symbol)
            if not price:
                continue

            current_volume = float(positions.get(vt_symbol, 0))
            target_volume = floor_to(target_value / price, self.config.execution.min_volume)
            diff = target_volume - current_volume

            if not diff:
                continue

            if diff > 0:
                direction = Direction.LONG
                offset = Offset.OPEN
                order_price = price * (1 + self.config.execution.price_add)
            else:
                direction = Direction.SHORT
                offset = Offset.CLOSE
                order_price = price * (1 - self.config.execution.price_add)

            orders.append(
                PlannedOrder(
                    datetime=datetime.now().isoformat(timespec="seconds"),
                    vt_symbol=vt_symbol,
                    direction=direction.name,
                    offset=offset.name,
                    price=order_price,
                    volume=abs(diff),
                    signal=signal,
                    mode=self.config.execution.mode,
                )
            )

        return orders

    def _persist_paper_result(self, orders: list[PlannedOrder]) -> ExecutionResult:
        """Persist paper orders and update local positions immediately."""
        output_path = Path(self.config.execution.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        order_path = output_path.joinpath("paper_orders.csv")
        position_path = output_path.joinpath("paper_positions.json")

        positions = self._load_positions(position_path)
        write_header = not order_path.exists()

        with open(order_path, mode="a", newline="", encoding="UTF-8") as f:
            fieldnames = list(PlannedOrder.__dataclass_fields__.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()

            for order in orders:
                if order.direction == Direction.LONG.name:
                    positions[order.vt_symbol] = float(positions.get(order.vt_symbol, 0)) + order.volume
                else:
                    positions[order.vt_symbol] = float(positions.get(order.vt_symbol, 0)) - order.volume

                writer.writerow(asdict(order))

        with open(position_path, mode="w", encoding="UTF-8") as f:
            json.dump(positions, f, indent=4, ensure_ascii=False)

        return ExecutionResult(orders=orders, order_path=order_path, position_path=position_path)

    def _execute_live(self, orders: list[PlannedOrder]) -> None:
        """Send planned orders through a configured vn.py gateway."""
        execution = self.config.execution
        if not execution.allow_live_trading:
            raise RuntimeError("live trading requires execution.allow_live_trading=true")

        if not execution.gateway_module or not execution.gateway_class or not execution.gateway_name:
            raise RuntimeError("live trading requires gateway_module, gateway_class, and gateway_name")

        module = import_module(execution.gateway_module)
        gateway_class = getattr(module, execution.gateway_class)

        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        main_engine.add_gateway(gateway_class, execution.gateway_name)
        main_engine.connect(execution.gateway_setting, execution.gateway_name)

        try:
            for order in orders:
                symbol, exchange = extract_vt_symbol(order.vt_symbol)
                direction = Direction[order.direction]
                offset = Offset[order.offset]
                req = OrderRequest(
                    symbol=symbol,
                    exchange=exchange,
                    direction=direction,
                    offset=offset,
                    type=OrderType.LIMIT,
                    price=order.price,
                    volume=order.volume,
                    reference="vnpym",
                )
                order.vt_orderid = main_engine.send_order(req, execution.gateway_name)
        finally:
            main_engine.close()

    def _load_latest_prices(self) -> dict[str, float]:
        """Load latest close prices from local lab data."""
        prices: dict[str, float] = {}
        interval = Interval(self.config.interval)
        start = parse_date(self.config.start)
        end = parse_date(self.config.end)

        for vt_symbol in self.config.symbols:
            bars = self.lab.load_bar_data(vt_symbol, interval, start, end)
            if bars:
                prices[vt_symbol] = bars[-1].close_price

        return prices

    def _load_positions(self, path: Path | None = None) -> dict[str, float]:
        """Load paper positions from disk."""
        if path is None:
            path = Path(self.config.execution.output_path).joinpath("paper_positions.json")

        if not path.exists():
            return {}

        with open(path, encoding="UTF-8") as f:
            data: dict[str, Any] = json.load(f)

        return {symbol: float(volume) for symbol, volume in data.items()}
