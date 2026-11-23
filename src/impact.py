import numpy as np
import pandas as pd


def add_loss_fields(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """Realised exposure and loss from outcome fields. Used only for LGD/EAD estimation and impact
    analysis, never as PD model inputs."""
    out = df.copy()
    is_bad = out[target] == 1
    out["ead_at_default"] = np.where(is_bad, (out["funded_amnt"] - out["total_rec_prncp"]).clip(lower=0), 0.0)
    net_recovery = (out["recoveries"] - out["collection_recovery_fee"]).clip(lower=0)
    out["realised_loss"] = np.where(is_bad, (out["ead_at_default"] - net_recovery).clip(lower=0), 0.0)
    # Cash returned to the lender over the loan's life, net of collection costs.
    out["cash_in"] = (
        out["total_rec_prncp"] + out["total_rec_int"] + out["total_rec_late_fee"]
        + out["recoveries"] - out["collection_recovery_fee"]
    )
    return out


def lgd_and_ead_factor(df: pd.DataFrame, target: str) -> dict:
    bads = df[df[target] == 1]
    return {
        "defaults": len(bads),
        "lgd": bads["realised_loss"].sum() / bads["ead_at_default"].sum(),
        "ead_factor": bads["ead_at_default"].sum() / bads["funded_amnt"].sum(),
    }


def cutoff_table(df: pd.DataFrame, risk: np.ndarray, target: str, approval_rates, expected_loss=None) -> pd.DataFrame:
    """Approve the lowest-risk share of loans; report what the approved portfolio would have looked like."""
    order = np.argsort(np.asarray(risk), kind="stable")
    y = df[target].to_numpy()[order]
    funded = df["funded_amnt"].to_numpy()[order]
    loss = df["realised_loss"].to_numpy()[order]
    cash = df["cash_in"].to_numpy()[order]
    el = None if expected_loss is None else np.asarray(expected_loss)[order]
    total_bads, total_goods = y.sum(), (1 - y).sum()
    rows = []
    for rate in approval_rates:
        k = int(round(rate * len(y)))
        approved = slice(0, k)
        row = {
            "approval_rate_pct": 100 * rate,
            "approved_loans": k,
            "bad_rate_pct": 100 * y[approved].mean(),
            "bads_avoided_pct": 100 * (1 - y[approved].sum() / total_bads),
            "goods_rejected_pct": 100 * (1 - (1 - y[approved]).sum() / total_goods),
            "realised_loss_rate_pct": 100 * loss[approved].sum() / funded[approved].sum(),
            "net_return_pct": 100 * (cash[approved].sum() / funded[approved].sum() - 1),
        }
        if el is not None:
            row["expected_loss_rate_pct"] = 100 * el[approved].sum() / funded[approved].sum()
        rows.append(row)
    return pd.DataFrame(rows).set_index("approval_rate_pct")
