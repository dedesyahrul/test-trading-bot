#!/usr/bin/env python3
"""
Offline LightGBM training script for MemeX prediction engine.

Usage:
    cd backend
    python scripts/train_model.py [--days 30] [--synthetic]

Extracts features + labels from PostgreSQL, trains a binary classifier,
and saves artifact to models/artifacts/momentum_scalp_v1.pkl
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
import lightgbm as lgb

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.prediction.engine import FEATURE_COLUMNS, MODEL_DIR, DEFAULT_MODEL

ARTIFACT_PATH = MODEL_DIR / DEFAULT_MODEL


def _generate_synthetic(n: int = 2000) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training data when DB has insufficient rows."""
    rng = np.random.default_rng(42)
    X = rng.normal(0, 1, (n, len(FEATURE_COLUMNS)))
    # Positive label when momentum + volume_spike are high
    momentum_idx = FEATURE_COLUMNS.index("momentum_1h")
    spike_idx = FEATURE_COLUMNS.index("volume_spike")
    score = X[:, momentum_idx] * 0.4 + X[:, spike_idx] * 0.6
    y = (score > 0.5).astype(int)
    return X, y


def _load_from_db(days: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Load features and generate labels from market snapshots."""
    try:
        from sqlalchemy import create_engine, text

        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://memex:memex@localhost:15487/memex",
        )
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        if not sync_url.startswith("postgresql+psycopg2"):
            sync_url = sync_url.replace("postgresql://", "postgresql+psycopg2://", 1)

        engine = create_engine(sync_url)
        since = datetime.utcnow() - timedelta(days=days)

        feature_cols = ", ".join(f"f.{c}" for c in FEATURE_COLUMNS)
        query = text(f"""
            SELECT {feature_cols},
                   f.pair_id, f.timestamp,
                   ms.price_usd AS entry_price
            FROM features f
            JOIN market_snapshots ms ON ms.pair_id = f.pair_id
                AND ms.timestamp = (
                    SELECT MIN(ms2.timestamp) FROM market_snapshots ms2
                    WHERE ms2.pair_id = f.pair_id AND ms2.timestamp >= f.timestamp
                )
            WHERE f.timestamp >= :since
            ORDER BY f.timestamp
            LIMIT 50000
        """)

        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"since": since})

        if len(df) < 100:
            return None

        # Label: +15% TP before -10% SL within next snapshots (simplified proxy)
        labels = []
        X_rows = []
        for _, row in df.iterrows():
            features = [float(row[c] or 0) for c in FEATURE_COLUMNS]
            # Proxy label from feature signals
            label = 1 if (features[4] > 0.05 and features[7] > 1.5) else 0
            X_rows.append(features)
            labels.append(label)

        return np.array(X_rows), np.array(labels)
    except Exception as e:
        print(f"DB load failed: {e}")
        return None


def train(days: int = 30, use_synthetic: bool = False) -> dict:
    data = None if use_synthetic else _load_from_db(days)
    if data is None:
        print("Using synthetic training data...")
        X, y = _generate_synthetic()
    else:
        X, y = data
        print(f"Loaded {len(y)} samples from database")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)) if len(set(y_test)) > 1 else 0.0,
        "train_samples": len(y_train),
        "test_samples": len(y_test),
        "positive_rate": float(y.mean()),
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACT_PATH)
    print(f"Model saved to {ARTIFACT_PATH}")
    print(f"Metrics: {metrics}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MemeX LightGBM model")
    parser.add_argument("--days", type=int, default=30, help="Days of historical data")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic data")
    args = parser.parse_args()
    train(days=args.days, use_synthetic=args.synthetic)
