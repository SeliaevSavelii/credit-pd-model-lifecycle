import numpy as np
import pandas as pd

from src import validation as val

# Declared before looking at 2015 results; conventions to be agreed with the model owner.
THRESHOLDS = pd.DataFrame(
    {
        "amber": [0.10, 0.10, 0.05, 0.05, 0.05],
        "red": [0.25, 0.25, 0.10, 0.01, 0.10],
    },
    index=pd.Index(
        [
            "score PSI",
            "feature CSI",
            "Gini drop vs development (absolute)",
            "calibration: Jeffreys p-value (below)",
            "calibration: relative PD underestimation (above)",
        ],
        name="metric",
    ),
)
RAG_RANK = {"green": 0, "amber": 1, "red": 2}


def rag_stability(value: float) -> str:
    t = THRESHOLDS.loc["score PSI"]
    return "red" if value > t["red"] else "amber" if value > t["amber"] else "green"


def rag_gini(drop: float) -> str:
    t = THRESHOLDS.loc["Gini drop vs development (absolute)"]
    return "red" if drop > t["red"] else "amber" if drop > t["amber"] else "green"


def rag_calibration(p_value: float, relative_gap: float) -> str:
    """A breach needs both statistical evidence and a material gap: with ~70k loans per quarter
    a p-value alone flags differences too small to matter."""
    p = THRESHOLDS.loc["calibration: Jeffreys p-value (below)"]
    gap = THRESHOLDS.loc["calibration: relative PD underestimation (above)"]
    if p_value < p["red"] and relative_gap >= gap["red"]:
        return "red"
    if p_value < p["amber"] and relative_gap >= gap["amber"]:
        return "amber"
    return "green"


def worst(statuses) -> str:
    return max(statuses, key=RAG_RANK.get)


def binned_shares(values, edges: np.ndarray) -> np.ndarray:
    bins = val.assign_grades(np.asarray(values), edges)
    return np.bincount(bins, minlength=len(edges))[1:] / len(bins)


def score_psi(pd_reference, pd_current, edges: np.ndarray) -> float:
    return val.psi(binned_shares(pd_reference, edges), binned_shares(pd_current, edges))


def label_shares(labels: pd.Series, categories) -> np.ndarray:
    return labels.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy()


def csi_by_period(ref_bins: pd.DataFrame, cur_bins: pd.DataFrame, periods: pd.Series) -> pd.DataFrame:
    """CSI per feature (rows) and period (columns), using the scorecard's own bins."""
    out = {}
    for period, idx in cur_bins.groupby(periods.to_numpy()).groups.items():
        current = cur_bins.loc[idx]
        out[period] = {}
        for f in ref_bins.columns:
            categories = sorted(set(ref_bins[f].astype(str)) | set(current[f].astype(str)))
            out[period][f] = val.psi(label_shares(ref_bins[f], categories), label_shares(current[f], categories))
    return pd.DataFrame(out)
