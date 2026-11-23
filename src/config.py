from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

KAGGLE_DATASET = "wordsforthewise/lending-club"
LOANS_PATH = PROCESSED_DIR / "loans_36m_2012_2015.parquet"

SAMPLES = {
    "development": ("2012-Q4", "2013-Q4"),
    "oot": ("2014-Q1", "2014-Q4"),
    "monitoring": ("2015-Q1", "2015-Q4"),
}
BAD_STATUSES = ("Charged Off", "Default", "Late (31-120 days)")
GOOD_STATUSES = ("Fully Paid",)
TARGET = "bad_flag"
VALID_SHARE = 0.3
RANDOM_STATE = 42

# Every source column must belong to exactly one group; the remainder are candidate model inputs.
ID_AND_FREE_TEXT = [
    "id", "member_id", "url", "desc", "title", "emp_title",
]

FAIRNESS_PROXY = [
    "zip_code", "addr_state",
]

# Lending Club's own risk assessment: benchmark only, never a model input.
LC_RISK_ASSESSMENT = [
    "grade", "sub_grade", "int_rate", "installment",
]

# Platform or administrative fields that carry no borrower information or duplicate loan_amnt.
ADMINISTRATIVE = [
    "funded_amnt", "funded_amnt_inv", "term", "issue_d", "policy_code",
    "initial_list_status", "disbursement_method", "application_type",
]

# Known only after origination: using them would leak the outcome.
POST_ORIGINATION_LEAKAGE = [
    "loan_status", "pymnt_plan", "out_prncp", "out_prncp_inv",
    "total_pymnt", "total_pymnt_inv", "total_rec_prncp", "total_rec_int",
    "total_rec_late_fee", "recoveries", "collection_recovery_fee",
    "last_pymnt_d", "last_pymnt_amnt", "next_pymnt_d", "last_credit_pull_d",
    "last_fico_range_high", "last_fico_range_low",
    "hardship_flag", "hardship_type", "hardship_reason", "hardship_status",
    "deferral_term", "hardship_amount", "hardship_start_date", "hardship_end_date",
    "payment_plan_start_date", "hardship_length", "hardship_dpd",
    "hardship_loan_status", "orig_projected_additional_accrued_interest",
    "hardship_payoff_balance_amount", "hardship_last_payment_amount",
    "debt_settlement_flag", "debt_settlement_flag_date", "settlement_status",
    "settlement_date", "settlement_amount", "settlement_percentage", "settlement_term",
]

# Only populated for joint applications, which are excluded from scope.
JOINT_APPLICATION = [
    "annual_inc_joint", "dti_joint", "verification_status_joint", "revol_bal_joint",
    "sec_app_fico_range_low", "sec_app_fico_range_high", "sec_app_earliest_cr_line",
    "sec_app_inq_last_6mths", "sec_app_mort_acc", "sec_app_open_acc",
    "sec_app_revol_util", "sec_app_open_act_il", "sec_app_num_rev_accts",
    "sec_app_chargeoff_within_12_mths", "sec_app_collections_12_mths_ex_med",
    "sec_app_mths_since_last_major_derog",
]

# Introduced by Lending Club in late 2015: entirely missing in development and OOT.
UNAVAILABLE_IN_DEVELOPMENT = [
    "open_acc_6m", "open_act_il", "open_il_12m", "open_il_24m", "mths_since_rcnt_il",
    "total_bal_il", "il_util", "open_rv_12m", "open_rv_24m", "max_bal_bc", "all_util",
    "inq_fi", "total_cu_tl", "inq_last_12m",
]

DERIVED = [
    "issue_date", "issue_year", "issue_quarter", "sample", TARGET,
]

COLUMN_GROUPS = {
    "id_or_free_text": ID_AND_FREE_TEXT,
    "fairness_proxy": FAIRNESS_PROXY,
    "lc_risk_assessment": LC_RISK_ASSESSMENT,
    "administrative": ADMINISTRATIVE,
    "post_origination_leakage": POST_ORIGINATION_LEAKAGE,
    "joint_application": JOINT_APPLICATION,
    "unavailable_in_development": UNAVAILABLE_IN_DEVELOPMENT,
    "derived": DERIVED,
}
