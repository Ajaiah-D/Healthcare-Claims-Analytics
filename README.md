# Healthcare Claims Analytics

**[View Tableau Dashboard](#)** ← link to be added on completion

---

End-to-end analysis of synthetic Medicare claims using the CMS DE-SynPUF (Data Entrepreneurs' Synthetic Public Use File) dataset. The project covers 2008–2010 and includes ~116,000 synthetic beneficiaries across inpatient, outpatient, and Part D prescription drug claims.

The analysis focuses on four areas:
- **Cost drivers** — which diagnoses (ICD-9), procedures (HCPCS/DRG), and provider patterns drive the highest reimbursements
- **Readmission patterns** — 30-day inpatient readmissions by condition and DRG
- **Chronic condition burden** — comorbidity across 11 CMS-flagged conditions (diabetes, CHF, COPD, CKD, cancer, Alzheimer's, depression, ischemic heart disease, osteoporosis, rheumatoid arthritis, stroke/TIA) and their effect on total spending
- **Utilization trends** — inpatient vs. outpatient vs. Part D utilization over the three-year window

---

## Data

All files are synthetic and were released by CMS for public use. Place them in `data/raw/` before running any notebooks. **Do not commit raw data to source control** — `data/` is gitignored.

| Table | File | Key fields |
|---|---|---|
| `inpatient_claims` | `DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv` | `DESYNPUF_ID`, `CLM_FROM_DT`, `CLM_THRU_DT`, `CLM_PMT_AMT`, `CLM_DRG_CD`, `CLM_ADMSN_DT`, `NCH_BENE_DSCHRG_DT`, ICD-9 dx×10, ICD-9 px×6, HCPCS×45 |
| `outpatient_claims` | `DE1_0_2008_to_2010_Outpatient_Claims_Sample_1.csv` | `DESYNPUF_ID`, `CLM_FROM_DT`, `CLM_PMT_AMT`, ICD-9 dx×10, HCPCS×45 |
| `beneficiary_summary` | `DE1_0_200{8,9,10}_Beneficiary_Summary_File_Sample_1.csv` | `DESYNPUF_ID`, demographics, `SP_*` chronic condition flags×11, `MEDREIMB_IP/OP/CAR`, `BENRES_*` |
| `prescription_drug_events` | `DE1_0_2008_to_2010_Prescription_Drug_Events_Sample_1.csv` | `DESYNPUF_ID`, `SRVC_DT`, `PROD_SRVC_ID`, `QTY_DSPNSD_NUM`, `DAYS_SUPLY_NUM`, `TOT_RX_CST_AMT`, `PTNT_PAY_AMT` |

Primary join key across all tables: **`DESYNPUF_ID`**

---

## Project Structure

```
data/
  raw/        # source CSVs — not committed
  cleaned/    # processed and merged tables
  exports/    # aggregates exported for Tableau
notebooks/
  01_setup.ipynb          # load CSVs → SQLite (cms_data.db)
  02_eda.ipynb            # schema exploration, distributions, missingness
  03_cost_analysis.ipynb  # cost drivers by DRG, ICD-9, provider
  04_readmissions.ipynb   # 30-day readmission detection and profiling
  05_chronic_conditions.ipynb  # comorbidity burden and cost impact
  06_exports.ipynb        # final aggregates → data/exports/ for Tableau
dashboard/
  # Tableau workbook (.twbx)
```

---

## Setup

```bash
pip install -r requirements.txt
jupyter notebook
```

Open `notebooks/01_setup.ipynb` first — it loads all source files into a local SQLite database (`cms_data.db`) and confirms row counts and column names for each table.

---

## Notes

- This dataset is **fully synthetic**. It contains no real patient data and is intended for analytical and educational use only.
- The beneficiary summary exists as three separate annual files (2008, 2009, 2010) and is stacked into a single table with a year column in the setup notebook.
- Cost fields reflect Medicare reimbursement amounts, not billed charges.
