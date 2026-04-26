# CMS DE-SynPUF Column Definitions

Reference guide for all columns across the four main tables. Keep this open while analyzing.

---

## Inpatient Claims

| Column | Definition | Type | Notes |
|---|---|---|---|
| `DESYNPUF_ID` | Beneficiary synthetic ID | int | Join key — unique per patient across all tables |
| `CLM_ID` | Unique claim identifier | int | — |
| `SEGMENT` | Claim line segment number | int | A single hospital stay can span multiple claim segments |
| `CLM_FROM_DT` | Claim start date | string (YYYYMMDD) | Format: 20080115 = Jan 15, 2008 |
| `CLM_THRU_DT` | Claim end/through date | string (YYYYMMDD) | — |
| `PRVDR_NUM` | Provider/facility ID | string | Identifies the hospital |
| `CLM_PMT_AMT` | **Medicare paid amount** | float | What Medicare reimbursed for this claim |
| `NCH_PRMRY_PYR_CLM_PD_AMT` | Primary payer (non-Medicare) amount | float | Usually $0 (Medicare is primary). Non-zero if patient has other insurance |
| `AT_PHYSN_NPI` | Attending physician NPI | string | National Provider ID of attending physician |
| `OP_PHYSN_NPI` | Operating physician NPI | string | NPI of surgeon/operating physician |
| `OT_PHYSN_NPI` | Other physician NPI | string | NPI of other involved physician |
| `CLM_ADMSN_DT` | Hospital admission date | string (YYYYMMDD) | Actual day patient entered hospital |
| `ADMTNG_ICD9_DGNS_CD` | Admitting diagnosis code | string | ICD-9 diagnosis that caused the admission |
| `CLM_PASS_THRU_PER_DIEM_AMT` | Pass-through per diem amount | float | Capital/direct medical education costs |
| `NCH_BENE_IP_DDCTBL_AMT` | **Beneficiary deductible amount** | float | What patient owes toward Part A deductible |
| `NCH_BENE_PTA_COINSRNC_LBLTY_AM` | **Beneficiary coinsurance amount** | float | What patient owes as coinsurance (% of cost after deductible) |
| `NCH_BENE_BLOOD_DDCTBL_LBLTY_AM` | Blood deductible liability | float | Patient's share of blood deductible |
| `CLM_UTLZTN_DAY_CNT` | **Length of stay (LOS)** | int | Number of days patient stayed |
| `NCH_BENE_DSCHRG_DT` | Discharge date | string (YYYYMMDD) | Day patient left hospital |
| `CLM_DRG_CD` | **Diagnosis Related Group code** | string | DRG classification — determines inpatient payment rate |
| `ICD9_DGNS_CD_1` through `ICD9_DGNS_CD_10` | Secondary diagnosis codes | string | Up to 10 ICD-9 codes describing patient conditions |
| `ICD9_PRCDR_CD_1` through `ICD9_PRCDR_CD_6` | Procedure codes | string | Up to 6 ICD-9 codes for procedures performed |
| `HCPCS_CD_1` through `HCPCS_CD_45` | Healthcare procedure codes | string | HCPCS codes for line-item services (up to 45) |

---

## Outpatient Claims

Same structure as inpatient, with these differences/additions:

| Column | Definition | Type | Notes |
|---|---|---|---|
| `NCH_BENE_PTB_DDCTBL_AMT` | **Beneficiary Part B deductible** | float | Outpatient is Part B coverage, not Part A |
| `NCH_BENE_PTB_COINSRNC_AMT` | **Beneficiary Part B coinsurance** | float | Usually 20% of allowed amount |
| `ADMTNG_ICD9_DGNS_CD` | Referring diagnosis | string | Reason for the outpatient visit (not admission diagnosis) |

**Omitted (inpatient only):**
- `CLM_ADMSN_DT`, `NCH_BENE_DSCHRG_DT`, `CLM_DRG_CD`, `CLM_UTLZTN_DAY_CNT` — no admission/discharge or DRG for outpatient
- `CLM_PASS_THRU_PER_DIEM_AMT` — no per diem for outpatient

---

## Beneficiary Summary

Annual snapshot per beneficiary. Files are split by year (2008, 2009, 2010), stacked into one table with a `YEAR` column.

| Column | Definition | Type | Notes |
|---|---|---|---|
| `YEAR` | Calendar year | int | 2008, 2009, or 2010 (added during load) |
| `DESYNPUF_ID` | Beneficiary synthetic ID | int | Join key |
| `BENE_BIRTH_DT` | Date of birth | string (YYYYMMDD) | — |
| `BENE_DEATH_DT` | Date of death | string (YYYYMMDD) | Blank if alive during that year |
| `BENE_SEX_IDENT_CD` | Sex | int | 1 = Male, 2 = Female |
| `BENE_RACE_CD` | Race | int | 1 = White, 2 = Black, 3 = Other, 4 = Asian, 5 = Hispanic, 6 = Native American |
| `BENE_ESRD_IND` | End-Stage Renal Disease indicator | string | Y = has ESRD, N = no |
| `SP_STATE_CODE` | State FIPS code | int | 01 = AL, 02 = AK, ..., 56 = WY |
| `BENE_COUNTY_CD` | County code | int | County within the state |
| `BENE_HI_CVRAGE_TOT_MONS` | Part A coverage months | int | Months enrolled in hospital insurance (0–12) |
| `BENE_SMI_CVRAGE_TOT_MONS` | Part B coverage months | int | Months enrolled in medical insurance (0–12) |
| `BENE_HMO_CVRAGE_TOT_MONS` | HMO coverage months | int | Months in Medicare Advantage (0–12) |
| `PLAN_CVRG_MOS_NUM` | Part D coverage months | int | Months in Part D drug plan (0–12) |
| **Chronic Condition Flags** | — | — | **1 = has condition, 2 = does not** |
| `SP_ALZHDMTA` | Alzheimer's/dementia | int | — |
| `SP_CHF` | Congestive heart failure | int | — |
| `SP_CHRNKIDN` | Chronic kidney disease | int | — |
| `SP_CNCR` | Cancer | int | — |
| `SP_COPD` | COPD | int | — |
| `SP_DEPRESSN` | Depression | int | — |
| `SP_DIABETES` | Diabetes | int | — |
| `SP_ISCHMCHT` | Ischemic heart disease | int | — |
| `SP_OSTEOPRS` | Osteoporosis | int | — |
| `SP_RA_OA` | Rheumatoid arthritis / osteoarthritis | int | — |
| `SP_STRKETIA` | Stroke / TIA | int | — |
| **Annual Cost Rollups** | — | — | — |
| `MEDREIMB_IP` | **Medicare inpatient reimbursement** | float | Total $ Medicare paid for inpatient that year |
| `BENRES_IP` | **Beneficiary inpatient responsibility** | float | Total $ patient paid for inpatient |
| `PPPYMT_IP` | Third-party inpatient payment | float | Total $ other insurance paid for inpatient |
| `MEDREIMB_OP` | Medicare outpatient reimbursement | float | Total $ Medicare paid for outpatient that year |
| `BENRES_OP` | Beneficiary outpatient responsibility | float | Total $ patient paid for outpatient |
| `PPPYMT_OP` | Third-party outpatient payment | float | Total $ other insurance paid for outpatient |
| `MEDREIMB_CAR` | Medicare carrier reimbursement | float | Total $ Medicare paid for carrier (physician/DME) that year |
| `BENRES_CAR` | Beneficiary carrier responsibility | float | Total $ patient paid for carrier |
| `PPPYMT_CAR` | Third-party carrier payment | float | Total $ other insurance paid for carrier |

---

## Prescription Drug Events

One row per drug dispensed. Multiple rows per beneficiary per year.

| Column | Definition | Type | Notes |
|---|---|---|---|
| `DESYNPUF_ID` | Beneficiary synthetic ID | int | Join key |
| `PDE_ID` | Prescription Drug Event ID | int | Unique ID for this drug dispensing |
| `SRVC_DT` | Service date (dispense date) | string (YYYYMMDD) | When the pharmacy filled the prescription |
| `PROD_SRVC_ID` | **Product/Service ID (NDC)** | string | National Drug Code — identifies the exact drug |
| `QTY_DSPNSD_NUM` | Quantity dispensed | int | Number of units (tablets, ml, etc.) |
| `DAYS_SUPLY_NUM` | Days supply | int | Number of days the prescription covers (e.g., 30, 90) |
| `PTNT_PAY_AMT` | **Patient pay amount** | float | What the beneficiary paid out-of-pocket |
| `TOT_RX_CST_AMT` | **Total drug cost** | float | Total cost (patient + plan + any other payers) |

---

## Key Relationships

### Join across tables:
All tables join on `DESYNPUF_ID`:
```sql
SELECT 
  b.DESYNPUF_ID,
  b.BENE_BIRTH_DT,
  b.SP_DIABETES,
  SUM(ip.CLM_PMT_AMT) as inpatient_cost,
  SUM(op.CLM_PMT_AMT) as outpatient_cost,
  COUNT(rx.PROD_SRVC_ID) as num_drugs
FROM beneficiary_summary b
LEFT JOIN inpatient_claims ip ON b.DESYNPUF_ID = ip.DESYNPUF_ID
LEFT JOIN outpatient_claims op ON b.DESYNPUF_ID = op.DESYNPUF_ID
LEFT JOIN prescription_drug_events rx ON b.DESYNPUF_ID = rx.DESYNPUF_ID
GROUP BY b.DESYNPUF_ID
```

### Cost hierarchy:
- **Claims-level detail** (inpatient/outpatient/prescription tables): row per claim/event, `CLM_PMT_AMT` or `TOT_RX_CST_AMT`
- **Annual summary** (beneficiary_summary table): pre-aggregated `MEDREIMB_*` columns

Use annual summary for quick comparisons, use claims-level detail for deep-dive analysis (e.g., "which DRGs cost the most?").

---

## Common Pitfalls

| Issue | Why | Fix |
|---|---|---|
| Negative `MEDREIMB_*` | Adjustment/credit issued | Keep in analysis — it's real activity |
| Missing `BENE_DEATH_DT` | Patient alive | Treat as blank/NULL, not an error |
| `HCPCS_CD_1` through `_45` mostly blank | Not all 45 codes used | Expected — typical claim uses 2–5 codes |
| Multiple rows per `DESYNPUF_ID` in claims | Multiple claims per patient | Expected — use GROUP BY / aggregation |
| Date columns are strings, not dates | CMS format: YYYYMMDD | Convert with `pd.to_datetime()` or SQL CAST |
