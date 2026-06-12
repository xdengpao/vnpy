from __future__ import annotations

from dataclasses import dataclass

from .config import VnpymConfig
from .data import MarketDataService, SyncResult
from .execution import ExecutionResult, ExecutionService
from .training import TrainingResult, TrainingService


@dataclass
class PipelineResult:
    """Combined workflow result."""

    sync: SyncResult | None = None
    training: TrainingResult | None = None
    execution: ExecutionResult | None = None


class VnpymPipeline:
    """Run the market-data, training, and trading workflow."""

    def __init__(self, config: VnpymConfig) -> None:
        self.config: VnpymConfig = config

    def run(
        self,
        fetch: bool = False,
        sample: bool = False,
        train: bool = True,
        trade: bool = True,
    ) -> PipelineResult:
        """Run selected workflow stages."""
        result = PipelineResult()

        if fetch and sample:
            raise ValueError("fetch and sample cannot both be true")

        data_service = MarketDataService(self.config)
        if fetch:
            result.sync = data_service.sync_history()
        elif sample:
            result.sync = data_service.generate_sample_data()

        if train:
            result.training = TrainingService(self.config).train()

        if trade:
            result.execution = ExecutionService(self.config).execute()

        return result
