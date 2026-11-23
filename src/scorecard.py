from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from optbinning import BinningProcess
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Scaling: 600 points at good:bad odds of 50:1, odds double every 20 points.
BASE_SCORE = 600
BASE_ODDS = 50
PDO = 20
FACTOR = PDO / np.log(2)
OFFSET = BASE_SCORE - FACTOR * np.log(BASE_ODDS)


def fit_binning(X: pd.DataFrame, y: pd.Series, features: list[str], categorical: list[str]) -> BinningProcess:
    numeric_params = {"monotonic_trend": "auto_asc_desc"}
    binning = BinningProcess(
        variable_names=features,
        categorical_variables=[c for c in categorical if c in features],
        min_bin_size=0.05,
        max_n_bins=8,
        binning_fit_params={f: numeric_params for f in features if f not in categorical},
    )
    return binning.fit(X[features], y)


def woe_transform(binning: BinningProcess, X: pd.DataFrame) -> pd.DataFrame:
    # "empirical" gives missing values the WoE of their own bin instead of 0.
    return binning.transform(
        X[binning.variable_names], metric="woe",
        metric_missing="empirical", metric_special="empirical",
    )


def fit_logit(X: pd.DataFrame, y: pd.Series):
    return sm.Logit(y.to_numpy(), sm.add_constant(X, has_constant="add")).fit(disp=0)


def vif_table(X: pd.DataFrame) -> pd.Series:
    Xc = sm.add_constant(X, has_constant="add").to_numpy()
    return pd.Series(
        [variance_inflation_factor(Xc, i + 1) for i in range(X.shape[1])],
        index=X.columns, name="vif",
    )


def select_features(
    woe: pd.DataFrame,
    y: pd.Series,
    iv: pd.Series,
    min_iv: float = 0.02,
    max_corr: float = 0.6,
    max_features: int = 15,
    max_pvalue: float = 0.01,
) -> tuple[list[str], pd.DataFrame]:
    """IV filter -> correlation pruning -> top-N by IV -> backward elimination on sign and p-value.

    With optbinning's WoE (higher = safer), every coefficient in a model of `bad` must be negative.
    """
    fate = {}
    ranked = iv.sort_values(ascending=False)
    for f in ranked[ranked < min_iv].index:
        fate[f] = f"IV {ranked[f]:.3f} < {min_iv}"

    corr = woe[ranked[ranked >= min_iv].index].corr().abs()
    kept: list[str] = []
    for f in ranked[ranked >= min_iv].index:
        clash = [k for k in kept if corr.loc[f, k] > max_corr]
        if clash:
            fate[f] = f"|corr| {corr.loc[f, clash[0]]:.2f} with {clash[0]}"
        else:
            kept.append(f)

    for f in kept[max_features:]:
        fate[f] = f"outside top {max_features} by IV"
    kept = kept[:max_features]

    while True:
        model = fit_logit(woe[kept], y)
        coefs = model.params.drop("const")
        pvalues = model.pvalues.drop("const")
        if (coefs > 0).any():
            drop = coefs.idxmax()
            fate[drop] = f"wrong sign (coef {coefs[drop]:+.3f}) in multivariate model"
        elif pvalues.max() > max_pvalue:
            drop = pvalues.idxmax()
            fate[drop] = f"p-value {pvalues[drop]:.3f} > {max_pvalue}"
        else:
            break
        kept.remove(drop)

    for f in kept:
        fate[f] = "selected"
    table = pd.DataFrame({"iv": ranked, "decision": pd.Series(fate)}).sort_values("iv", ascending=False)
    return kept, table


@dataclass
class Scorecard:
    binning: BinningProcess
    model: object
    features: list[str]

    def woe(self, X: pd.DataFrame) -> pd.DataFrame:
        return woe_transform(self.binning, X)[self.features]

    def log_odds_bad(self, X: pd.DataFrame) -> np.ndarray:
        coefs = self.model.params
        return coefs["const"] + self.woe(X).to_numpy() @ coefs[self.features].to_numpy()

    def predict_pd(self, X: pd.DataFrame) -> np.ndarray:
        return 1 / (1 + np.exp(-self.log_odds_bad(X)))

    def score(self, X: pd.DataFrame) -> np.ndarray:
        return OFFSET - FACTOR * self.log_odds_bad(X)

    def points_table(self) -> pd.DataFrame:
        coefs = self.model.params
        base_per_feature = (OFFSET - FACTOR * coefs["const"]) / len(self.features)
        rows = []
        for f in self.features:
            table = self.binning.get_binned_variable(f).binning_table.build()
            table = table.drop(index="Totals")
            for _, row in table.iterrows():
                woe = row["WoE"] if row["Count"] > 0 else 0.0
                is_category_group = not isinstance(row["Bin"], str)
                rows.append({
                    "feature": f,
                    "bin": ", ".join(map(str, row["Bin"])) if is_category_group else row["Bin"],
                    # Matches binning.transform(metric="bins") output, used for lookups.
                    "bin_key": str(row["Bin"]),
                    "count_pct": round(100 * row["Count (%)"], 2),
                    "bad_rate_pct": round(100 * row["Event rate"], 2) if row["Count"] > 0 else np.nan,
                    "woe": round(woe, 4),
                    "points": round(base_per_feature - FACTOR * coefs[f] * woe),
                })
        return pd.DataFrame(rows)
