from __future__ import annotations

import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from vnpy.alpha.lab import AlphaLab
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData

from .config import VnpymConfig, parse_date


FEATURE_COLUMNS = [
    "ret_1",
    "ret_5",
    "ret_window",
    "ma_ratio",
    "volatility",
    "volume_ratio",
]


@dataclass
class ModelArtifact:
    """Persisted trained model with metadata."""

    model: Any
    feature_columns: list[str]
    trained_at: datetime
    metrics: dict[str, float]

    def predict(self, df: pl.DataFrame) -> np.ndarray:
        """Predict signal values for a feature frame."""
        data = df.select(self.feature_columns).to_numpy()
        return cast(np.ndarray, self.model.predict(data))


@dataclass
class TrainingResult:
    """Result of one training run."""

    model_path: Path
    signal_path: Path
    metrics: dict[str, float]
    rows: int


class TrainingService:
    """Train models and generate ranking signals from local market data."""

    def __init__(self, config: VnpymConfig) -> None:
        self.config: VnpymConfig = config
        self.lab: AlphaLab = AlphaLab(config.lab_path)

    def train(self) -> TrainingResult:
        """Build features, train the model, and persist signals."""
        feature_df = build_feature_frame(self.lab, self.config)
        train_df, valid_df = split_train_valid(feature_df, self.config.training.valid_ratio)

        model = Pipeline(
            steps=[
                ("scale", StandardScaler()),
                ("ridge", Ridge(alpha=self.config.training.ridge_alpha)),
            ]
        )

        x_train = train_df.select(FEATURE_COLUMNS).to_numpy()
        y_train = np.asarray(train_df["label"])
        model.fit(x_train, y_train)

        train_pred = model.predict(x_train)
        valid_pred = model.predict(valid_df.select(FEATURE_COLUMNS).to_numpy())
        y_valid = np.asarray(valid_df["label"])

        metrics = {
            "train_r2": float(r2_score(y_train, train_pred)),
            "valid_r2": float(r2_score(y_valid, valid_pred)),
            "valid_mse": float(mean_squared_error(y_valid, valid_pred)),
        }

        artifact = ModelArtifact(
            model=model,
            feature_columns=list(FEATURE_COLUMNS),
            trained_at=datetime.now(),
            metrics=metrics,
        )

        model_path = self.model_path
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, mode="wb") as f:
            pickle.dump(artifact, f)

        signal_df = generate_signal_frame(feature_df, artifact)
        self.lab.save_signal(self.config.training.signal_name, signal_df)

        return TrainingResult(
            model_path=model_path,
            signal_path=self.signal_path,
            metrics=metrics,
            rows=feature_df.height,
        )

    def load_model(self) -> ModelArtifact:
        """Load the persisted model artifact."""
        with open(self.model_path, mode="rb") as f:
            artifact: ModelArtifact = pickle.load(f)
        return artifact

    @property
    def model_path(self) -> Path:
        """Return model artifact path."""
        return Path(self.config.lab_path).joinpath("model", f"{self.config.training.model_name}.pkl")

    @property
    def signal_path(self) -> Path:
        """Return signal artifact path."""
        return Path(self.config.lab_path).joinpath("signal", f"{self.config.training.signal_name}.parquet")


def build_feature_frame(lab: AlphaLab, config: VnpymConfig) -> pl.DataFrame:
    """Build model-ready features and forward-return labels from lab bars."""
    interval = Interval(config.interval)
    start = parse_date(config.start)
    end = parse_date(config.end)
    rows: list[dict[str, Any]] = []

    for vt_symbol in config.symbols:
        bars: list[BarData] = lab.load_bar_data(vt_symbol, interval, start, end)
        for bar in bars:
            rows.append(
                {
                    "datetime": bar.datetime,
                    "vt_symbol": vt_symbol,
                    "open": bar.open_price,
                    "high": bar.high_price,
                    "low": bar.low_price,
                    "close": bar.close_price,
                    "volume": bar.volume,
                    "turnover": bar.turnover,
                }
            )

    if not rows:
        raise RuntimeError("no local bars found; run fetch, sample, or import-csv first")

    df = pl.DataFrame(rows).sort(["vt_symbol", "datetime"])
    window = config.training.feature_window
    horizon = config.training.label_horizon

    df = df.with_columns(
        [
            (pl.col("close") / pl.col("close").shift(1).over("vt_symbol") - 1).alias("ret_1"),
            (pl.col("close") / pl.col("close").shift(5).over("vt_symbol") - 1).alias("ret_5"),
            (pl.col("close") / pl.col("close").shift(window).over("vt_symbol") - 1).alias("ret_window"),
            (pl.col("close") / pl.col("close").rolling_mean(window).over("vt_symbol") - 1).alias("ma_ratio"),
            (pl.col("close").shift(-horizon).over("vt_symbol") / pl.col("close") - 1).alias("label"),
        ]
    )

    df = df.with_columns(
        [
            pl.col("ret_1").rolling_std(window).over("vt_symbol").alias("volatility"),
            (
                pl.col("volume") / pl.col("volume").rolling_mean(window).over("vt_symbol") - 1
            ).alias("volume_ratio"),
        ]
    )

    finite_columns = FEATURE_COLUMNS + ["label"]
    filters = [pl.col(column).is_finite() for column in finite_columns]
    return df.filter(pl.all_horizontal(filters)).sort(["datetime", "vt_symbol"])


def split_train_valid(df: pl.DataFrame, valid_ratio: float) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Split by datetime to avoid leakage across the validation boundary."""
    dates = sorted(df["datetime"].unique().to_list())
    if len(dates) < 3:
        raise RuntimeError("not enough dates to split training and validation data")

    valid_count = max(1, int(len(dates) * valid_ratio))
    split_date = dates[-valid_count]
    train_df = df.filter(pl.col("datetime") < split_date)
    valid_df = df.filter(pl.col("datetime") >= split_date)

    if train_df.is_empty() or valid_df.is_empty():
        raise RuntimeError("empty train or validation split")

    return train_df, valid_df


def generate_signal_frame(df: pl.DataFrame, artifact: ModelArtifact) -> pl.DataFrame:
    """Generate prediction signal frame from a trained artifact."""
    signals = artifact.predict(df)
    return (
        df.select(["datetime", "vt_symbol"])
        .with_columns(pl.Series("signal", signals))
        .sort(["datetime", "signal"], descending=[False, True])
    )
