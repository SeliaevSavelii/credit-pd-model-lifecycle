import numpy as np
import pandas as pd
from scipy.stats import beta, binomtest, chi2, ks_2samp, norm, rankdata
from sklearn.metrics import roc_auc_score
from statsmodels.stats.proportion import proportion_confint


def gini(y_true, y_score) -> float:
    return 2 * roc_auc_score(y_true, y_score) - 1


def ks_statistic(y_true, y_score) -> float:
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    return ks_2samp(y_score[y_true == 1], y_score[y_true == 0]).statistic


def bootstrap_gini_ci(y_true, y_score, n_boot: int = 200, level: float = 0.95, seed: int = 0) -> tuple[float, float]:
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    rng = np.random.default_rng(seed)
    n = len(y_true)
    ginis = [gini(y_true[idx], y_score[idx]) for idx in (rng.integers(0, n, n) for _ in range(n_boot))]
    alpha = (1 - level) / 2
    return float(np.quantile(ginis, alpha)), float(np.quantile(ginis, 1 - alpha))


def delong_test(y_true, score_a, score_b) -> dict:
    """Paired DeLong test for two AUCs on the same loans (fast midrank algorithm, Sun & Xu 2014)."""
    y = np.asarray(y_true).astype(bool)
    scores = np.vstack([np.asarray(score_a, float), np.asarray(score_b, float)])
    pos, neg = scores[:, y], scores[:, ~y]
    m, n = pos.shape[1], neg.shape[1]
    aucs, v_pos, v_neg = [], [], []
    for k in range(2):
        rank_pos = rankdata(pos[k])
        rank_neg = rankdata(neg[k])
        rank_all = rankdata(np.concatenate([pos[k], neg[k]]))
        aucs.append((rank_all[:m].sum() - m * (m + 1) / 2) / (m * n))
        v_pos.append((rank_all[:m] - rank_pos) / n)
        v_neg.append(1 - (rank_all[m:] - rank_neg) / m)
    cov = np.cov(np.array(v_pos)) / m + np.cov(np.array(v_neg)) / n
    diff = aucs[0] - aucs[1]
    var = cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]
    se = np.sqrt(var) if var > 0 else 0.0
    z = diff / se if se > 0 else 0.0
    return {
        "gini_a": 2 * aucs[0] - 1,
        "gini_b": 2 * aucs[1] - 1,
        "gini_diff": 2 * diff,
        "gini_diff_ci_low": 2 * (diff - 1.96 * se),
        "gini_diff_ci_high": 2 * (diff + 1.96 * se),
        "z": z,
        "p_value": 2 * norm.sf(abs(z)) if se > 0 else 1.0,
    }


def jeffreys_pvalue(n: int, defaults: int, pd_estimate: float) -> float:
    """One-sided: small p-value means observed defaults are significantly above the predicted PD."""
    return float(beta.cdf(pd_estimate, defaults + 0.5, n - defaults + 0.5))


def binomial_pvalue(n: int, defaults: int, pd_estimate: float) -> float:
    return float(binomtest(defaults, n, pd_estimate, alternative="greater").pvalue)


def grade_edges(pd_reference, n_grades: int = 8) -> np.ndarray:
    """Equal-population PD bands fixed on the reference sample (a simple master scale)."""
    inner = np.quantile(np.asarray(pd_reference), np.linspace(0, 1, n_grades + 1)[1:-1])
    return np.concatenate([[0.0], inner, [1.0]])


def assign_grades(pd_values, edges: np.ndarray) -> np.ndarray:
    return np.clip(np.searchsorted(edges, pd_values, side="right"), 1, len(edges) - 1)


def calibration_table(y_true, pd_values, grades) -> pd.DataFrame:
    df = pd.DataFrame({"y": np.asarray(y_true), "pd": np.asarray(pd_values), "grade": np.asarray(grades)})
    rows = []
    for grade, g in df.groupby("grade"):
        n, d, mean_pd = len(g), int(g["y"].sum()), g["pd"].mean()
        low, high = proportion_confint(d, n, method="wilson")
        rows.append({
            "grade": grade, "loans": n, "defaults": d,
            "mean_pd_pct": 100 * mean_pd, "odr_pct": 100 * d / n,
            "odr_ci_low_pct": 100 * low, "odr_ci_high_pct": 100 * high,
            "binomial_p": binomial_pvalue(n, d, mean_pd),
            "jeffreys_p": jeffreys_pvalue(n, d, mean_pd),
        })
    return pd.DataFrame(rows).set_index("grade")


def hosmer_lemeshow(y_true, pd_values, groups: int = 10) -> dict:
    df = pd.DataFrame({"y": np.asarray(y_true), "pd": np.asarray(pd_values)})
    df["group"] = pd.qcut(df["pd"], groups, labels=False, duplicates="drop")
    agg = df.groupby("group").agg(n=("y", "size"), observed=("y", "sum"), expected=("pd", "sum"))
    stat = (((agg["observed"] - agg["expected"]) ** 2) / (agg["expected"] * (1 - agg["expected"] / agg["n"]))).sum()
    dof = len(agg) - 2
    return {"statistic": float(stat), "dof": dof, "p_value": float(chi2.sf(stat, dof))}


def psi(expected_share, actual_share, eps: float = 1e-6) -> float:
    """Population Stability Index from bin shares of the reference (expected) and current (actual) sample."""
    e = np.clip(np.asarray(expected_share, float), eps, None)
    a = np.clip(np.asarray(actual_share, float), eps, None)
    return float(np.sum((a - e) * np.log(a / e)))
