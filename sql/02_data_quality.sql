CREATE OR REPLACE VIEW loans AS
SELECT * FROM read_parquet('{processed_path}');

-- Outcome status mix per issue year: shows maturity and what the target excludes.
CREATE OR REPLACE VIEW dq_status_by_year AS
SELECT
    issue_year,
    loan_status,
    COUNT(*) AS n,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY issue_year), 2) AS pct_of_year
FROM loans
GROUP BY issue_year, loan_status
ORDER BY issue_year, n DESC;

-- Vintage table: volumes, exclusions and bad rate per issue quarter.
CREATE OR REPLACE VIEW dq_vintage AS
SELECT
    sample,
    issue_quarter,
    COUNT(*) AS n_total,
    COUNT(*) FILTER (WHERE bad_flag IS NULL) AS n_excluded,
    COUNT(*) FILTER (WHERE bad_flag = 0) AS n_good,
    COUNT(*) FILTER (WHERE bad_flag = 1) AS n_bad,
    ROUND(100.0 * COUNT(*) FILTER (WHERE bad_flag IS NULL) / COUNT(*), 2) AS pct_excluded,
    ROUND(100.0 * AVG(bad_flag), 2) AS bad_rate_pct
FROM loans
GROUP BY sample, issue_quarter
ORDER BY issue_quarter;

CREATE OR REPLACE VIEW dq_application_type AS
SELECT issue_year, application_type, COUNT(*) AS n
FROM loans
GROUP BY issue_year, application_type
ORDER BY issue_year, application_type;

CREATE OR REPLACE VIEW dq_duplicate_ids AS
SELECT id, COUNT(*) AS n
FROM loans
GROUP BY id
HAVING COUNT(*) > 1;

CREATE OR REPLACE VIEW dq_ranges AS
SELECT
    MIN(annual_inc) AS min_annual_inc,
    MAX(annual_inc) AS max_annual_inc,
    COUNT(*) FILTER (WHERE annual_inc <= 0) AS n_income_nonpositive,
    MIN(dti) AS min_dti,
    MAX(dti) AS max_dti,
    COUNT(*) FILTER (WHERE dti < 0 OR dti > 100) AS n_dti_out_of_range,
    MAX(revol_util) AS max_revol_util,
    COUNT(*) FILTER (WHERE revol_util > 100) AS n_revol_util_over_100,
    MIN(fico_range_low) AS min_fico,
    MAX(fico_range_high) AS max_fico,
    MIN(loan_amnt) AS min_loan_amnt,
    MAX(loan_amnt) AS max_loan_amnt
FROM loans;
