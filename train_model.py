"""Genuine Random Forest Regression training pipeline for WasteWise AI.

Key ML safeguards:
- Uses ONLY features available BEFORE food preparation (zero data leakage).
- Chronological train/test split (first 80% past -> last 20% recent).
- Evaluates real MAE and RMSE on held-out test records.
- Persists trained sklearn Pipeline and metadata via joblib/JSON.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.config import (
    ARTIFACTS_DIR,
    MIN_NEW_RECORDS_FOR_RETRAIN,
    MIN_TRAINING_RECORDS,
    MODEL_ARTIFACT_PATH,
    MODEL_METADATA_PATH,
)
from app.database.base import DatabaseRepository

CATEGORICAL_FEATURES = ["food_item", "day_of_week"]
NUMERIC_FEATURES = [
    "expected_attendance",
    "special_event",
    "holiday",
    "previous_sales",
    "is_weekend",
]
TARGET_COLUMN = "sold_quantity"


def _prepare_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Clean records and build strict pre-preparation feature columns."""
    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Chronological sort to guarantee time-ordered split and prevent leakage
    df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce")
    df = df.dropna(subset=["record_date", "food_item", "day_of_week", TARGET_COLUMN]).copy()
    df = df.sort_values(["record_date", "id"] if "id" in df.columns else ["record_date"]).reset_index(drop=True)

    df["expected_attendance"] = pd.to_numeric(df["expected_attendance"], errors="coerce").fillna(0).clip(lower=0)
    df["special_event"] = pd.to_numeric(df["special_event"], errors="coerce").fillna(0).clip(0, 1).astype(int)
    df["holiday"] = pd.to_numeric(df["holiday"], errors="coerce").fillna(0).clip(0, 1).astype(int)
    df["previous_sales"] = pd.to_numeric(df["previous_sales"], errors="coerce").fillna(0).clip(lower=0)
    df["is_weekend"] = df["day_of_week"].isin(["Saturday", "Sunday"]).astype(int)
    df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce").fillna(0).clip(lower=0)

    return df


def _aggregate_feature_importances(pipeline: Pipeline) -> list[dict[str, Any]]:
    """Aggregate one-hot encoded and numeric importances into clean human concepts."""
    preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
    regressor: RandomForestRegressor = pipeline.named_steps["regressor"]
    feature_names = preprocessor.get_feature_names_out()
    importances = regressor.feature_importances_

    grouped: dict[str, float] = {
        "Food Item": 0.0,
        "Day of Week": 0.0,
        "Expected Attendance": 0.0,
        "Previous Sales": 0.0,
        "Special Event": 0.0,
        "Holiday": 0.0,
        "Weekend Indicator": 0.0,
    }

    for fname, imp in zip(feature_names, importances):
        if fname.startswith("cat__food_item_"):
            grouped["Food Item"] += float(imp)
        elif fname.startswith("cat__day_of_week_"):
            grouped["Day of Week"] += float(imp)
        elif fname == "num__expected_attendance":
            grouped["Expected Attendance"] += float(imp)
        elif fname == "num__previous_sales":
            grouped["Previous Sales"] += float(imp)
        elif fname == "num__special_event":
            grouped["Special Event"] += float(imp)
        elif fname == "num__holiday":
            grouped["Holiday"] += float(imp)
        elif fname == "num__is_weekend":
            grouped["Weekend Indicator"] += float(imp)

    return [
        {"feature": k, "importance_pct": round(v * 100, 1)}
        for k, v in sorted(grouped.items(), key=lambda x: x[1], reverse=True)
    ]


def load_model_metadata() -> dict[str, Any]:
    """Load saved model metadata or return an uninitialized status structure."""
    if MODEL_METADATA_PATH.exists():
        try:
            with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "status": "not_trained",
        "model_version": "uninitialized",
        "algorithm": "RandomForestRegressor",
        "mae": None,
        "rmse": None,
        "r2_score": None,
        "train_size": 0,
        "test_size": 0,
        "total_records_at_train": 0,
        "live_records_at_train": 0,
        "trained_at": None,
        "feature_importances": [],
        "message": "Model has not been trained yet.",
    }


def save_model_metadata(metadata: dict[str, Any]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def train_demand_model(db: DatabaseRepository) -> dict[str, Any]:
    """Train Random Forest Regressor using chronological split and save artifacts."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_records = db.get_training_dataset()
    counts = db.count_sales_records()
    df = _prepare_dataframe(raw_records)

    if len(df) < MIN_TRAINING_RECORDS:
        metadata = {
            "status": "insufficient_data",
            "model_version": "none",
            "algorithm": "RandomForestRegressor",
            "mae": None,
            "rmse": None,
            "r2_score": None,
            "train_size": 0,
            "test_size": 0,
            "total_records_at_train": len(df),
            "live_records_at_train": counts["live_records"],
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "feature_importances": [],
            "message": (
                f"Insufficient training data: found {len(df)} records, "
                f"minimum {MIN_TRAINING_RECORDS} required to train reliably."
            ),
        }
        save_model_metadata(metadata)
        return metadata

    # Chronological 80% train / 20% test split (no shuffling to prevent leakage)
    split_idx = int(math.floor(len(df) * 0.8))
    split_idx = max(MIN_TRAINING_RECORDS - 10, min(split_idx, len(df) - 10))

    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    feature_cols = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    X_train, y_train = train_df[feature_cols], train_df[TARGET_COLUMN]
    X_test, y_test = test_df[feature_cols], test_df[TARGET_COLUMN]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=160,
                    max_depth=14,
                    min_samples_leaf=3,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    mae = round(float(mean_absolute_error(y_test, preds)), 2)
    rmse = round(float(root_mean_squared_error(y_test, preds)), 2)
    r2 = round(float(r2_score(y_test, preds)), 4)
    importances = _aggregate_feature_importances(pipeline)

    model_version = f"rf-v{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    joblib.dump(pipeline, MODEL_ARTIFACT_PATH)

    metadata = {
        "status": "ready",
        "model_version": model_version,
        "algorithm": "RandomForestRegressor (scikit-learn)",
        "mae": mae,
        "rmse": rmse,
        "r2_score": r2,
        "train_size": int(len(train_df)),
        "test_size": int(len(test_df)),
        "total_records_at_train": int(len(df)),
        "live_records_at_train": int(counts["live_records"]),
        "train_date_range": f"{train_df['record_date'].min().date().isoformat()} to {train_df['record_date'].max().date().isoformat()}",
        "test_date_range": f"{test_df['record_date'].min().date().isoformat()} to {test_df['record_date'].max().date().isoformat()}",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features_used": feature_cols,
        "feature_importances": importances,
        "min_new_records_for_retrain": MIN_NEW_RECORDS_FOR_RETRAIN,
        "explanation": (
            "The Random Forest model estimates meal demand from historical sales patterns and "
            "pre-preparation context (food item, day of week, expected attendance, special events, "
            "holidays, and prior sales). Actual results should always be reviewed by the canteen manager."
        ),
        "message": f"Model trained on {len(train_df)} records and evaluated on {len(test_df)} chronological test records.",
    }
    save_model_metadata(metadata)
    return metadata


def get_model_status(db: DatabaseRepository) -> dict[str, Any]:
    """Combine saved model metadata with current live DB record counts."""
    metadata = load_model_metadata()
    counts = db.count_sales_records()
    total_now = counts["total_records"]
    live_now = counts["live_records"]
    live_at_train = int(metadata.get("live_records_at_train", 0))
    new_live_since_train = max(0, live_now - live_at_train)
    model_exists = MODEL_ARTIFACT_PATH.exists()

    if total_now < MIN_TRAINING_RECORDS or not model_exists or metadata.get("status") != "ready":
        status = "insufficient_data" if total_now < MIN_TRAINING_RECORDS else "not_trained"
    else:
        status = "ready"

    return {
        **metadata,
        "status": status,
        "model_file_present": model_exists,
        "current_total_records": total_now,
        "current_synthetic_records": counts["synthetic_records"],
        "current_live_records": live_now,
        "new_live_records_since_train": new_live_since_train,
        "min_training_records": MIN_TRAINING_RECORDS,
        "min_new_records_for_retrain": MIN_NEW_RECORDS_FOR_RETRAIN,
        "ready_for_retrain": (
            total_now >= MIN_TRAINING_RECORDS and new_live_since_train >= MIN_NEW_RECORDS_FOR_RETRAIN
        ),
    }


if __name__ == "__main__":
    from app.database import db as default_db
    from app.database.init_db import init_database

    init_database(force_reset=False)
    result = train_demand_model(default_db)
    print(json.dumps(result, indent=2))
