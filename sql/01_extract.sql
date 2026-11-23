-- Extract 36-month loans issued 2012-2015, assign samples and the target.
-- Rows with an immature/ambiguous status keep bad_flag = NULL so their share can be reported.
COPY (
    WITH src AS (
        SELECT *
        FROM read_csv('{raw_path}', header = true, sample_size = -1)
    ),
    typed AS (
        SELECT
            *,
            CAST(strptime(issue_d, '%b-%Y') AS DATE) AS issue_date
        FROM src
        WHERE issue_d IS NOT NULL
          AND trim(term) = '36 months'
    )
    SELECT
        *,
        year(issue_date) AS issue_year,
        year(issue_date) || '-Q' || quarter(issue_date) AS issue_quarter,
        -- Bureau fields were rolled out during 2012-Q1..Q3, so development starts at 2012-Q4.
        CASE
            WHEN issue_date < DATE '2012-10-01' THEN 'pre_development'
            WHEN year(issue_date) <= 2013 THEN 'development'
            WHEN year(issue_date) = 2014 THEN 'oot'
            WHEN year(issue_date) = 2015 THEN 'monitoring'
        END AS sample,
        CASE
            WHEN loan_status IN ('Charged Off', 'Default', 'Late (31-120 days)') THEN 1
            WHEN loan_status = 'Fully Paid' THEN 0
        END AS bad_flag
    FROM typed
    WHERE year(issue_date) BETWEEN 2012 AND 2015
) TO '{out_path}' (FORMAT parquet);
