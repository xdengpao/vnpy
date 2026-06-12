from __future__ import annotations

import argparse
from pathlib import Path

from .config import create_default_config, load_config
from .data import MarketDataService, available_crypto_gateways
from .execution import ExecutionService
from .pipeline import VnpymPipeline
from .training import TrainingService


def main() -> None:
    """Run vnpym command line interface."""
    parser = argparse.ArgumentParser(prog="vnpym")
    parser.add_argument("--config", default="examples/vnpym/config.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init")
    subparsers.add_parser("sample")
    fetch_parser = subparsers.add_parser("fetch")
    fetch_parser.add_argument("--source", choices=["datafeed", "crypto_gateway"])
    fetch_parser.add_argument("--crypto-exchange")

    subparsers.add_parser("crypto-exchanges")
    subparsers.add_parser("train")
    subparsers.add_parser("trade")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--fetch", action="store_true")
    run_parser.add_argument("--sample", action="store_true")
    run_parser.add_argument("--no-trade", action="store_true")
    run_parser.add_argument("--source", choices=["datafeed", "crypto_gateway"])
    run_parser.add_argument("--crypto-exchange")

    csv_parser = subparsers.add_parser("import-csv")
    csv_parser.add_argument("path")
    csv_parser.add_argument("vt_symbol")

    args = parser.parse_args()
    config_path = Path(args.config)

    if args.command == "init":
        create_default_config(config_path)
        print(f"created config: {config_path}")
        return

    if args.command == "crypto-exchanges":
        for name, description in available_crypto_gateways().items():
            print(f"{name}: {description}")
        return

    config = load_config(config_path)

    if args.command == "sample":
        sync_result = MarketDataService(config).generate_sample_data()
        print(f"generated sample bars: {sync_result.total} {sync_result.counts}")
    elif args.command == "fetch":
        if args.source:
            config.datafeed.source = args.source
        if args.crypto_exchange:
            config.crypto_gateway.name = args.crypto_exchange
        sync_result = MarketDataService(config).sync_history()
        print(f"fetched bars: {sync_result.total} {sync_result.counts}")
    elif args.command == "import-csv":
        count = MarketDataService(config).import_csv(args.path, args.vt_symbol)
        print(f"imported bars: {count}")
    elif args.command == "train":
        training_result = TrainingService(config).train()
        print(f"trained rows: {training_result.rows}")
        print(f"model: {training_result.model_path}")
        print(f"signal: {training_result.signal_path}")
        print(f"metrics: {training_result.metrics}")
    elif args.command == "trade":
        execution_result = ExecutionService(config).execute()
        print(f"orders: {len(execution_result.orders)}")
        print(f"order file: {execution_result.order_path}")
        print(f"position file: {execution_result.position_path}")
    elif args.command == "run":
        if args.source:
            config.datafeed.source = args.source
        if args.crypto_exchange:
            config.crypto_gateway.name = args.crypto_exchange
        pipeline_result = VnpymPipeline(config).run(
            fetch=args.fetch,
            sample=args.sample,
            train=True,
            trade=not args.no_trade,
        )
        if pipeline_result.sync:
            print(f"bars: {pipeline_result.sync.total} {pipeline_result.sync.counts}")
        if pipeline_result.training:
            print(f"model: {pipeline_result.training.model_path}")
            print(f"signal: {pipeline_result.training.signal_path}")
            print(f"metrics: {pipeline_result.training.metrics}")
        if pipeline_result.execution:
            print(f"orders: {len(pipeline_result.execution.orders)}")
            print(f"order file: {pipeline_result.execution.order_path}")


if __name__ == "__main__":
    main()
