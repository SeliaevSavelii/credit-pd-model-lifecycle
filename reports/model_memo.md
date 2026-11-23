# Memo: review of the consumer loan scorecard

To: Credit Committee
From: Savelii Seliaev
Data: Lending Club 36-month consumer loans, 2012–2015 (public data)

## Purpose

The scorecard gives each loan application a score for how likely the borrower is to stop repaying (the probability of default, PD). It is used for two decisions: which applications to approve, and how much loss to expect on the loans we hold.

## Summary

The scorecard ranks applicants reliably, but it underestimates how much risk there is in recent loans. In 2015 it expected about 13% of borrowers to default; about 15% did. I recommend keeping it for approval decisions, correcting its loss estimates now, and starting a redevelopment.

## How well does it work?

Of every 100 loans from 2015 that later defaulted, 35 had been placed in the riskiest 20% of applicants by the score. With a random ordering it would be 20.

On 2014 loans it ranked risk as well as Lending Club's own internal grade. It uses 13 standard credit-bureau and application characteristics, and each one works in an intuitive direction: for example, a lower credit score or higher debt relative to income means higher risk.

## Is it still reliable?

Quarterly monitoring of 2015 gives a mixed picture:

- Applicant profile: unchanged compared with the development period.
- Ranking of good versus bad borrowers: unchanged.
- Risk level: actual defaults were 11–18% higher than predicted in every quarter.

So the applicants look the same on paper but default more often. I found no data error. The most likely explanation is that the lender changed how it grew, priced loans and verified income, none of which is visible in application data. This kind of shift also shows up slowly: one year after a loan is issued, only about a third of the eventual defaults have happened.

## What it means financially (2015 loans, $3.6bn)

| | Expected loss | Actual loss |
|---|---|---|
| Current scorecard | $221M | $274M (24% higher) |
| With a simple correction | $233M | $274M (17% higher) |

Declining the riskiest 15% of applications would have lowered the default rate from 14.9% to 12.6% and the loss rate from 7.6% to 6.4%, and raised the lifetime return on approved loans from 6.35% to 6.90%. The cost is that about 13 in every 100 borrowers who would have repaid would also have been turned away.

## Limitations

- The data comes from a US peer-to-peer lender, not from our own portfolio.
- The model predicts default over the full 3-year loan term, not the 12-month horizon used for regulatory capital.
- Only approved loans are in the data, so we cannot say how rejected applicants would have behaved.
- Loss figures exclude funding and servicing costs, and the uncertainty estimates assume borrowers default independently, which understates real-world risk.
- No protected characteristics are used and location fields were left out, but the data does not allow a proper fairness test.

## Decisions requested

1. Approve a correction to the loss estimates (a risk add-on, ideally per risk segment) until the model is redeveloped.
2. Approve a redevelopment on recent loans. A more complex test model already gives about 0.25 percentage points more return at the same approval rate.
3. Agree an early-warning check: track the 12-month default rate of each quarter's loans, so a similar shift would be noticed after about one year rather than three.
