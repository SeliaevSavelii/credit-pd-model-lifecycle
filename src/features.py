import pandas as pd

from src.data_prep import classify_columns

CATEGORICAL = ["home_ownership", "verification_status", "purpose"]
REPLACED_BY_DERIVED = ["emp_length", "earliest_cr_line", "fico_range_low", "fico_range_high"]
DERIVED_FEATURES = ["emp_length_years", "credit_history_months", "loan_to_income", "fico_mid"]


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["emp_length_years"] = (
        out["emp_length"].str.replace("< 1 year", "0", regex=False)
        .str.extract(r"(\d+)")[0].astype(float)
    )
    earliest = pd.to_datetime(out["earliest_cr_line"], format="%b-%Y")
    issued = pd.to_datetime(out["issue_date"])
    out["credit_history_months"] = (
        (issued.dt.year - earliest.dt.year) * 12 + (issued.dt.month - earliest.dt.month)
    )
    out["loan_to_income"] = out["loan_amnt"] / out["annual_inc"]
    out["fico_mid"] = (out["fico_range_low"] + out["fico_range_high"]) / 2
    out["home_ownership"] = out["home_ownership"].replace({"NONE": "OTHER", "ANY": "OTHER"})
    return out


def candidate_features(columns: list[str]) -> list[str]:
    audit = classify_columns(columns)
    raw = audit.loc[audit["group"] == "candidate_feature", "column"].tolist()
    excluded = set(REPLACED_BY_DERIVED) | set(DERIVED_FEATURES)
    return [c for c in raw if c not in excluded] + DERIVED_FEATURES
