from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from src import config

PARAMS = dict(
    objective="binary",
    learning_rate=0.03,
    n_estimators=3000,
    num_leaves=31,
    min_child_samples=200,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=config.RANDOM_STATE,
    verbose=-1,
)


@dataclass
class Challenger:
    model: lgb.LGBMClassifier
    features: list[str]
    categories: dict[str, list]

    def frame(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X[self.features].copy()
        for col, cats in self.categories.items():
            out[col] = pd.Categorical(out[col], categories=cats)
        return out

    def predict_pd(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(self.frame(X))[:, 1]


def fit_challenger(
    train: pd.DataFrame, valid: pd.DataFrame, features: list[str], categorical: list[str], target: str,
) -> Challenger:
    categories = {c: sorted(train[c].dropna().unique()) for c in categorical if c in features}
    challenger = Challenger(lgb.LGBMClassifier(**PARAMS), features, categories)
    # Validation is used for early stopping, so only OOT performance is a clean test.
    challenger.model.fit(
        challenger.frame(train), train[target],
        eval_X=challenger.frame(valid),
        eval_y=valid[target],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(100, verbose=False)],
    )
    return challenger
