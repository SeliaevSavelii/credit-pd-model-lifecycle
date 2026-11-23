# Validation Report — Consumer Loan PD Scorecard

Technical companion to the [model memo](model_memo.md). All numbers are reproduced by `python run_all.py`; source notebooks are referenced per section.

---

## 1. Purpose and scope

| Item | Definition |
|---|---|
| Model purpose | Rank applicants by default risk and estimate a PD for approval and expected-loss use |
| Product | Lending Club unsecured consumer loans, 36-month term, individual applications |
| Outcome ("bad") | `Charged Off`, `Default` or `Late (31–120 days)`; "good" = `Fully Paid`; other statuses excluded |
| Horizon | Lifetime (36-month) default, not a 12-month PD |
| Model type | Logistic regression on Weight-of-Evidence (WoE) bins, scaled to a points scorecard |
| Samples | Development 2012-Q4–2013 (70/30 train/validation), out-of-time (OOT) 2014, monitoring 2015 by quarter |

## 2. Data (notebook 01)

**Source.** Kaggle `wordsforthewise/lending-club`, accepted loans 2007–2018Q4 (CC0). Extracted with DuckDB SQL (`sql/01_extract.sql`) to 36-month loans issued 2012–2015.

| Sample | Period | Loans | Bads | Bad rate (95% Wilson CI) |
|---|---|---|---|---|
| Development | 2012-Q4–2013-Q4 | 115,603 | 14,327 | 12.39% (12.20–12.58) |
| Out-of-time | 2014 | 162,570 | 22,315 | 13.73% (13.56–13.89) |
| Monitoring | 2015 | 282,848 | 42,150 | 14.90% (14.77–15.04) |

**Data-quality findings.**
- About 25 bureau fields were not collected before 2012-Q3 (100% missing in 2012-Q1/Q2), so development starts at **2012-Q4**; 2012-Q1–Q3 is excluded.
- 14 fields introduced in 2015-Q4 (e.g. `open_acc_6m`, `il_util`) are excluded as unavailable at development.
- Outcomes are mature: only 86 loans (0.03%, all 2015) have unresolved statuses. `Default` never occurs; bads are almost entirely `Charged Off`.
- Invalid values set to missing: income ≤ 0 (2 loans), DTI outside 0–100 (5 loans). `revol_util` > 100% (2,208 loans) is plausible and kept.
- No duplicate IDs; 239 joint applications (2015 only) excluded.
- Minimum FICO is 660: only loans accepted by Lending Club are observed (no reject inference).

## 3. Column audit and leakage control (notebook 01, `src/config.py`)

Every one of the 151 source columns is assigned to exactly one group, enforced in code:

| Group | Columns | Treatment |
|---|---|---|
| Candidate features (application-time) | 62 | Eligible as inputs |
| Post-origination (payments, recoveries, last FICO, hardship, settlement) | 39 | Excluded as outcome leakage; recoveries/payments used only for LGD/EAD estimation |
| Lending Club risk assessment (`grade`, `sub_grade`, `int_rate`, `installment`) | 4 | Benchmark only |
| Geography (`zip_code`, `addr_state`) | 2 | Excluded as potential proxies for protected characteristics |
| Joint-application, unavailable-in-development, administrative, IDs/free text | 44 | Excluded |

Derived features: employment length in years, credit-history length (months), loan-to-income, FICO midpoint.

## 4. Model development (notebook 02, `src/scorecard.py`)

**Binning.** `optbinning`, fitted on train only: monotonic event-rate trend for numeric features, ≥ 5% of loans per bin, ≤ 8 bins; missing values form their own bin (missing `mths_since_*` means "event never occurred" and is informative).

**Selection.** 62 candidates → IV ≥ 0.02 (36 dropped) → drop features whose WoE correlates > 0.6 with a stronger kept feature (12 dropped) → backward elimination on wrong sign or p > 0.01 (1 dropped) → **13 features**, all VIF < 2.

| Feature | IV | Coefficient (WoE) |
|---|---|---|
| `fico_mid` | 0.126 | −0.509 |
| `annual_inc` | 0.105 | −0.327 |
| `bc_open_to_buy` | 0.084 | −0.508 |
| `tot_hi_cred_lim` | 0.082 | −0.503 |
| `dti` | 0.052 | −0.580 |
| `loan_to_income` | 0.046 | −0.845 |
| `acc_open_past_24mths` | 0.042 | −0.689 |
| `percent_bc_gt_75` | 0.041 | −0.298 |
| `mo_sin_rcnt_tl` | 0.036 | −0.310 |
| `mths_since_recent_inq` | 0.034 | −0.831 |
| `mths_since_recent_bc` | 0.030 | −0.507 |
| `mo_sin_old_il_acct` | 0.029 | −0.537 |
| `purpose` | 0.026 | −0.958 |
| Intercept | | −1.960 |

All coefficients are negative as required (higher WoE = lower risk) with p < 0.001. Individual IVs are modest, consistent with a population already screened by the lender; delinquency and public-record fields carry almost no information in the accepted population.

**Scaling.** 600 points at 50:1 good:bad odds, 20 points to double the odds. Summing rounded bin points reproduces the model score within 4 points (full table: `reports/scorecard_points.csv`).

## 5. Validation (notebook 03, `src/validation.py`)

### 5.1 Discrimination

| Sample | Gini (95% bootstrap CI) | KS |
|---|---|---|
| Train | 0.339 (0.329–0.350) | 0.246 |
| Validation | 0.326 (0.310–0.344) | 0.237 |
| OOT 2014 | 0.326 (0.318–0.332) | 0.233 |
| *Benchmark: LC `sub_grade`, OOT* | 0.319 (0.312–0.326) | 0.237 |
| *Benchmark: LC `int_rate`, OOT* | 0.315 (0.308–0.323) | 0.234 |

No overfitting (train–validation gap 1.3 Gini points) and no decay out of time. Paired DeLong test, LC `sub_grade` vs champion on OOT: −0.6 Gini points (95% CI −1.3 to +0.1), p = 0.08 → statistically equivalent.

### 5.2 Calibration

| Sample | Mean PD | Observed DR | Jeffreys p | Hosmer–Lemeshow p | Brier |
|---|---|---|---|---|---|
| Train | 12.39% | 12.39% | 0.50 | 0.37 | 0.104 |
| Validation | 12.43% | 12.39% | 0.59 | 0.53 | 0.105 |
| OOT 2014 | 13.01% | 13.73% | < 0.001 | < 0.001 | 0.114 |

OOT by grade (8 equal-population grades fixed on train):

| Grade | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Mean PD % | 3.77 | 6.37 | 8.37 | 10.28 | 12.36 | 14.80 | 18.07 | 25.45 |
| Observed DR % | 4.06 | 6.75 | 9.28 | 11.39 | 13.53 | 15.46 | 19.28 | 25.54 |
| Jeffreys p | 0.020 | 0.016 | <0.001 | <0.001 | <0.001 | 0.004 | <0.001 | 0.37 |

PD is significantly underestimated in 7 of 8 grades out of time. Tests are one-sided (risk of underestimation), and assume independent defaults; with correlated defaults the p-values overstate the evidence, so the size of the gap (~5% relative) is the more relevant figure. The mean PD rose 0.6 pp because the 2014 population is riskier on its features, but the observed rate rose 1.3 pp.

### 5.3 Challenger (`src/challenger.py`)

LightGBM with early stopping on the validation sample, compared on OOT with the paired DeLong test:

| Model | OOT Gini | Gain vs champion (95% CI) | p |
|---|---|---|---|
| Champion scorecard (13 features) | 0.326 | — | — |
| LightGBM, same 13 features | 0.336 | +1.0 (+0.7 to +1.3) | < 0.001 |
| LightGBM, all 62 candidates | 0.364 | +3.8 (+3.4 to +4.3) | < 0.001 |

About 1 point comes from the algorithm and 2.8 from information the scorecard did not use. SHAP values of the challenger and the exact linear contributions of the scorecard agree on the two strongest drivers (FICO, loan-to-income) and on the direction of every feature.

**Validation conclusion.** Champion retained: stable ranking equal to the LC benchmark and fully interpretable. Weakness: PD level out of time. Proposed recalibration: intercept shift +0.065 (odds × 1.067), estimated on 2014 and tested on 2015.

## 6. Monitoring (notebook 04, `src/monitoring.py`, `sql/03_monitoring_tables.sql`)

Thresholds declared before results: PSI/CSI amber 0.10, red 0.25; Gini drop amber 5, red 10 points; calibration amber/red when Jeffreys p < 0.05/0.01 **and** relative underestimation ≥ 5%/10%.

| 2015 | Score PSI | Max CSI | Gini | Mean PD | Observed DR | Underestimation | Status |
|---|---|---|---|---|---|---|---|
| Q1 | 0.017 | 0.051 | 0.328 | 13.31% | 14.83% | 11.4% | 🔴 calibration |
| Q2 | 0.011 | 0.068 | 0.332 | 13.12% | 15.38% | 17.2% | 🔴 calibration |
| Q3 | 0.005 | 0.072 | 0.346 | 12.74% | 14.58% | 14.5% | 🔴 calibration |
| Q4 | 0.003 | 0.083 | 0.340 | 12.56% | 14.87% | 18.3% | 🔴 calibration |

Stability and discrimination are green; calibration is red in all quarters. With the 2014 recalibration the underestimation falls to 6–12% (two quarters amber, two red). The SQL implementation reproduces the Python PSI and default rates to within 1e-17.

**Investigation.** No data or definition change. Of the +2.5 pp rise in default rate vs development, +0.5 pp is explained by the borrower mix and +2.0 pp is unexplained. The gap is concentrated in LC's riskier grades (−1.6 pp in A, +3.7 pp in C, +7.5 pp in D, +11 to +19 pp in E–G) and in verified-income loans; the share of "Source Verified" loans doubled (20% → 42%). LC's 36-month volume grew almost six-fold between 2012-Q4 and 2015-Q4 while its average interest rate fell from ~13% to ~11%. The gap is positive in 100 of 103 feature bins, i.e. a change in risk level and spread, not one broken feature.

**Time lag.** Only ~35% of eventual defaulters have stopped paying 12 months after issue (~78% after 24 months), so back-testing signals arrive with a long delay; front-end stability metrics are immediate but cannot detect this kind of shift.

## 7. Business impact (notebook 05, `src/impact.py`)

- **LGD 0.89** and **EAD factor 0.57** (outstanding principal at default / funded amount), estimated on development defaults; stable in 2015 (0.89, 0.58).
- **Expected vs realised loss, 2015** ($3.62bn funded): champion EL $221M vs realised $274M (shortfall $53M, 24%); recalibrated $233M (shortfall $40M); challenger $232M (shortfall $42M).
- **Cutoff at 85% approval (champion):** bad rate 14.9% → 12.6%, loss rate 7.56% → 6.38%, net lifetime return 6.35% → 6.90%; 27.9% of bads avoided, 12.7% of goods declined.
- **Challenger at 85%:** loss rate 6.05%, net return 7.15%. Swap set: the 15,208 loans only the champion approves have a 26.5% bad rate vs 21.7% for those only the challenger approves.
- Ranking by LC `int_rate` gives the lowest loss rate but the lowest return, because it declines the highest-yielding loans.

## 8. Limitations

1. Public US peer-to-peer lending data; results do not transfer to another lender's portfolio.
2. Lifetime default, not 12-month PD; no default date is available.
3. Accepted loans only (selection bias, no reject inference).
4. Calibration and AUC tests assume independent defaults.
5. LGD/EAD are portfolio averages; net return excludes funding, servicing and capital costs.
6. No protected-characteristic data, so fairness was addressed by exclusion of potential proxies, not by testing outcomes.
7. Real-time monitoring would observe 2015 outcomes only gradually; the recalibration test uses 2014 outcomes that would not be complete until 2017.

## 9. Recommendations

1. Apply a documented PD overlay for expected-loss use, evaluated at segment level (LC grade or verification status), not only a portfolio intercept shift.
2. Redevelop on recent vintages, re-testing features excluded by the IV and correlation rules.
3. Add an early-read back-test (12-month default rate per vintage) to shorten the detection lag.
4. Set approval cutoffs on risk-adjusted return, not on default rate alone.

## 10. Reproducibility

`python run_all.py` runs 9 unit tests (`tests/test_validation.py`), re-extracts the data and executes notebooks 01–05 in order (≈ 2 minutes). A full rerun reproduces every table in `reports/` exactly.
