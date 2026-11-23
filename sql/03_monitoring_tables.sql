-- Monitoring layer over scored loans written by notebook 04.
-- sample = 'reference' (development train) or 'monitoring' (2015).
CREATE OR REPLACE VIEW scored AS
SELECT * FROM read_parquet('{scored_path}');

-- Back-testing per quarter: volume, defaults, mean PD, observed default rate (ODR).
CREATE OR REPLACE VIEW mon_quarterly AS
SELECT
    issue_quarter,
    COUNT(*) AS loans,
    SUM(bad_flag) AS defaults,
    AVG(pd) AS mean_pd,
    AVG(bad_flag * 1.0) AS odr,
    AVG(bad_flag * 1.0) / AVG(pd) - 1 AS relative_underestimation
FROM scored
WHERE sample = 'monitoring'
GROUP BY issue_quarter
ORDER BY issue_quarter;

-- Back-testing per quarter and risk grade.
CREATE OR REPLACE VIEW mon_grade AS
SELECT
    issue_quarter,
    grade,
    COUNT(*) AS loans,
    SUM(bad_flag) AS defaults,
    AVG(pd) AS mean_pd,
    AVG(bad_flag * 1.0) AS odr
FROM scored
WHERE sample = 'monitoring'
GROUP BY issue_quarter, grade
ORDER BY issue_quarter, grade;

-- Front-end stability: PSI of the score per quarter against development score deciles.
CREATE OR REPLACE VIEW mon_score_psi AS
WITH ref AS (
    SELECT score_bin, COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS ref_share
    FROM scored
    WHERE sample = 'reference'
    GROUP BY score_bin
),
cur AS (
    SELECT
        issue_quarter,
        score_bin,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY issue_quarter) AS cur_share
    FROM scored
    WHERE sample = 'monitoring'
    GROUP BY issue_quarter, score_bin
)
SELECT
    cur.issue_quarter,
    SUM((cur.cur_share - ref.ref_share) * LN(cur.cur_share / ref.ref_share)) AS psi
FROM cur
JOIN ref USING (score_bin)
GROUP BY cur.issue_quarter
ORDER BY cur.issue_quarter;
