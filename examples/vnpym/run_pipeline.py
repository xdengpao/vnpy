from vnpy.vnpym import VnpymPipeline, load_config


def main() -> None:
    """Run a local sample-data pipeline."""
    config = load_config("examples/vnpym/config.json")
    result = VnpymPipeline(config).run(sample=True)

    if result.sync:
        print(f"bars: {result.sync.total}")

    if result.training:
        print(f"model: {result.training.model_path}")
        print(f"signal: {result.training.signal_path}")
        print(f"metrics: {result.training.metrics}")

    if result.execution:
        print(f"orders: {len(result.execution.orders)}")
        print(f"order file: {result.execution.order_path}")


if __name__ == "__main__":
    main()
