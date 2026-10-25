# Outlier Engine | Research Report

Generated (UTC): 2026-10-25T16:05:55+00:00

**Mode:** Synthetic demonstration. Not live prices, executable quotes, or investment advice.

## Agent assignments

- **SCOUT:** Identify candidate mismatches in paired YES/NO event contracts. Do not claim identical settlement rules without verification.
- **QUANT:** Compute gross spread and hypothetical net spread after specified fees; flag non-positive values and missing execution evidence.
- **SKEPTIC:** Try to falsify the opportunity: settlement differences, liquidity, slippage, fees, availability, jurisdiction, and operational failure.

## Candidate observations

### SYNTHETIC: Central bank decision scenario A

- YES: $0.43; NO: $0.51; estimated fees: $0.02
- Gross spread: 6.00%; estimated net spread: 4.00%
- **Status: RESEARCH ONLY. NOT CLEARED FOR EXECUTION.**
- Skeptic findings:
  - Settlement equivalence not independently verified
  - Simultaneous executable quotes and size not verified
  - Platform eligibility and jurisdiction not verified
  - Slippage, capital lockup, counterparty and tax risks remain

### SYNTHETIC: Economic release scenario C

- YES: $0.36; NO: $0.60; estimated fees: $0.03
- Gross spread: 4.00%; estimated net spread: 1.00%
- **Status: RESEARCH ONLY. NOT CLEARED FOR EXECUTION.**
- Skeptic findings:
  - Settlement equivalence not independently verified
  - Simultaneous executable quotes and size not verified
  - Platform eligibility and jurisdiction not verified
  - Slippage, capital lockup, counterparty and tax risks remain

### SYNTHETIC: Economic release scenario B

- YES: $0.58; NO: $0.44; estimated fees: $0.02
- Gross spread: -2.00%; estimated net spread: -4.00%
- **Status: RESEARCH ONLY. NOT CLEARED FOR EXECUTION.**
- Skeptic findings:
  - Settlement equivalence not independently verified
  - Simultaneous executable quotes and size not verified
  - Platform eligibility and jurisdiction not verified
  - No positive estimated spread after listed fees
  - Slippage, capital lockup, counterparty and tax risks remain

## Gate to live-data research

Require authenticated data provenance, timestamped executable quotes, matched settlement rules, fee schedules, order-book depth, platform eligibility, and independent out-of-sample testing.
