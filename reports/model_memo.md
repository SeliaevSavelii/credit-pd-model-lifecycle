# Memo: Consumer Loan Default Scorecard — Performance Review and Recommendation

**To:** Credit Committee  **From:** Savelii Seliaev  **Data:** Lending Club 36-month consumer loans, 2012–2015 (public data)

### 1. Purpose
The scorecard gives every loan application a score that estimates how likely the borrower is to stop repaying (the *probability of default*, PD). It supports two decisions: **which applications to approve**, and **how much loss to expect** from the loans we hold.

### 2. Bottom line
The scorecard **ranks applicants reliably**, but it **underestimates the level of risk** in recent loans: in 2015 it expected about 13% of borrowers to default, while about 15% did. I recommend continuing to use it for approval decisions, but correcting its loss estimates now and starting a redevelopment.

### 3. How good is it?
- Of every 100 loans issued in 2015 that later defaulted, **35 had been placed in the riskiest 20%** of applicants by the score (a random ordering would place 20).
- On 2014 loans it sorted risk as well as Lending Club's own internal grade, while using only 13 standard credit-bureau and application characteristics, each with an understandable effect (e.g. lower credit score or higher debt relative to income → higher risk).

### 4. Is it reliable over time?
Quarterly monitoring for 2015 shows a clear split:
- 🟢 **Applicant profile** unchanged versus the development period.
- 🟢 **Ranking** of good versus bad borrowers unchanged.
- 🔴 **Risk level:** actual defaults 11–18% higher than predicted in every quarter.

The applicants *look* the same on paper but default more. The checks found no data error; the most likely causes are changes in the lender's growth, pricing and income-verification practices, which application data cannot see. Note that this signal only becomes visible slowly: one year after a loan is issued, only about a third of its eventual defaults have happened.

### 5. Business effect (2015 loans, $3.6bn)
| | Expected loss | Actual loss |
|---|---|---|
| Current scorecard | $221M | **$274M** (24% higher) |
| With a simple correction | $233M | $274M (17% higher) |

Using the score to decline the riskiest 15% of applications would have cut the default rate from 14.9% to 12.6% and the loss rate from 7.6% to 6.4%, and **raised the lifetime return** on approved loans from 6.35% to 6.90%. It would also have turned away about 13 of every 100 borrowers who would have repaid.

### 6. Limitations
- Built on US peer-to-peer lending data, not on our own portfolio.
- Predicts default over the full 3-year loan term, not the 12-month horizon used for regulatory capital.
- Only approved loans are observed, so the effect on applicants the lender rejected is unknown.
- Loss figures are before funding and servicing costs; uncertainty measures assume borrowers default independently, which understates real-world risk.
- No protected characteristics are used and location fields were excluded; the data does not allow a formal fairness test.

### 7. Decisions requested
1. **Approve a correction to loss estimates** (a risk add-on, preferably by risk segment) until the model is redeveloped.
2. **Approve a redevelopment** on recent loans. A more complex benchmark model already shows about 0.25 percentage points higher return at the same approval rate.
3. **Agree an early-warning check**: track 12-month default rates per quarter, so the next shift is seen in about one year instead of three.
