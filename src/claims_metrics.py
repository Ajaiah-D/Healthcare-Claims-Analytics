"""Shared metric definitions for the Healthcare Claims Analytics notebooks.

Every notebook imports its labels, spend definition, readmission logic and
spending tiers from here so each metric is defined exactly once.
"""

import pandas as pd

CONDITION_LABELS = {
    'SP_ALZHDMTA': "Alzheimer's / Dementia",
    'SP_CHF': 'Heart Failure (CHF)',
    'SP_CHRNKIDN': 'Chronic Kidney Disease',
    'SP_CNCR': 'Cancer',
    'SP_COPD': 'COPD',
    'SP_DEPRESSN': 'Depression',
    'SP_DIABETES': 'Diabetes',
    'SP_ISCHMCHT': 'Ischemic Heart Disease',
    'SP_OSTEOPRS': 'Osteoporosis',
    'SP_RA_OA': 'Rheumatoid Arthritis / Osteoarthritis',
    'SP_STRKETIA': 'Stroke / TIA',
}
CHRONIC_COLS = list(CONDITION_LABELS)

# Annual Medicare reimbursement: inpatient + outpatient + carrier (physician).
# Excludes Part D drug cost and the beneficiary's own share.
TOTAL_SPEND_SQL = (
    "COALESCE(MEDREIMB_IP, 0) + COALESCE(MEDREIMB_OP, 0) + COALESCE(MEDREIMB_CAR, 0)"
)

READMISSION_WINDOW_DAYS = 30

# 'No spend' holds beneficiary-years with $0 (or net-negative adjustment) reimbursement.
TIER_BINS = [float('-inf'), 0, 500, 2000, 5000, 10000, float('inf')]
TIER_LABELS = ['No spend', '$0-500', '$500-2K', '$2K-5K', '$5K-10K', '$10K+']


def _sql_julianday(col: str) -> str:
    # Dates are stored as YYYYMMDD integers; julianday() returns NULL on those,
    # so rebuild 'YYYY-MM-DD' text first.
    return (
        f"julianday(substr({col}, 1, 4) || '-' || substr({col}, 5, 2) || '-' || substr({col}, 7, 2))"
    )


# SQL twin of flag_readmissions(): one row per inpatient stay with days to the
# same patient's next admission. Prefix a query with this to use `flagged`.
STAYS_FLAGGED_CTE = f"""
WITH stays AS (
  SELECT
    DESYNPUF_ID,
    CLM_ID,
    CLM_DRG_CD,
    CLM_PMT_AMT,
    {_sql_julianday('CLM_ADMSN_DT')} AS admit_jd,
    {_sql_julianday('NCH_BENE_DSCHRG_DT')} AS discharge_jd
  FROM inpatient_claims
  WHERE SEGMENT = 1
),
flagged AS (
  SELECT
    *,
    CAST(
      LEAD(admit_jd) OVER (PARTITION BY DESYNPUF_ID ORDER BY admit_jd, discharge_jd, CLM_ID)
      - discharge_jd
    AS INTEGER) AS days_to_next_admit
  FROM stays
)
"""

READMIT_FLAG_SQL = (
    f"CASE WHEN days_to_next_admit BETWEEN 1 AND {READMISSION_WINDOW_DAYS} THEN 1 ELSE 0 END"
)


def load_inpatient_stays(conn) -> pd.DataFrame:
    """One row per inpatient stay.

    A claim too long for one record is split into SEGMENT 1 and 2 sharing a
    CLM_ID; segment 1 carries the DRG and diagnosis, so it represents the stay.
    """
    return pd.read_sql(
        """
        SELECT
          DESYNPUF_ID,
          CLM_ID,
          CLM_ADMSN_DT,
          NCH_BENE_DSCHRG_DT,
          CLM_DRG_CD,
          ICD9_DGNS_CD_1,
          CLM_PMT_AMT
        FROM inpatient_claims
        WHERE SEGMENT = 1
        """,
        conn,
    )


def flag_readmissions(stays: pd.DataFrame) -> pd.DataFrame:
    """Flag each stay that is followed by a readmission within 30 days.

    The flag sits on the index stay (the one being discharged), which is the
    stay a readmission rate is attributed to. Gaps of 0 days (same-day
    transfers) and negative gaps (overlapping stays) are not readmissions.
    """
    if stays['CLM_ID'].duplicated().any():
        raise ValueError("stays must have one row per CLM_ID")

    df = stays.copy()
    for col in ('CLM_ADMSN_DT', 'NCH_BENE_DSCHRG_DT'):
        df[col] = pd.to_datetime(df[col].astype('int64').astype(str), format='%Y%m%d')

    df = df.sort_values(
        ['DESYNPUF_ID', 'CLM_ADMSN_DT', 'NCH_BENE_DSCHRG_DT', 'CLM_ID']
    ).reset_index(drop=True)

    df['next_admission_date'] = df.groupby('DESYNPUF_ID')['CLM_ADMSN_DT'].shift(-1)
    df['days_to_readmission'] = (df['next_admission_date'] - df['NCH_BENE_DSCHRG_DT']).dt.days
    df['readmitted_30d'] = df['days_to_readmission'].between(1, READMISSION_WINDOW_DAYS)
    return df


def attach_conditions(stays: pd.DataFrame, bene: pd.DataFrame) -> pd.DataFrame:
    """Attach each stay's chronic condition flags from the admission year.

    beneficiary_summary has one row per beneficiary per year, so the join key
    is (DESYNPUF_ID, YEAR). Joining on DESYNPUF_ID alone duplicates stays.
    """
    df = stays.copy()
    df['YEAR'] = df['CLM_ADMSN_DT'].dt.year
    return df.merge(bene, on=['DESYNPUF_ID', 'YEAR'], how='left', validate='many_to_one')


def spending_tier(total_spend: pd.Series) -> pd.Series:
    """Bucket annual spend into tiers; every row gets a tier."""
    return pd.cut(total_spend, bins=TIER_BINS, labels=TIER_LABELS)


def condition_impact(bene: pd.DataFrame, condition: str) -> dict:
    """Spend with vs. without one condition, at beneficiary-year grain.

    spend_delta is the raw difference in means, which is confounded: people
    with the condition also carry more of the other ten. adjusted_spend_delta
    compares with/without only among beneficiary-years that have the same
    number of *other* conditions, then averages those gaps weighted by where
    the with-condition group actually sits.
    """
    has = bene[condition] == 1
    with_cond = bene[has]
    without_cond = bene[bene[condition] == 2]

    row = {
        'condition': CONDITION_LABELS[condition],
        'beneficiary_years_with_condition': len(with_cond),
        'prevalence_pct': round(len(with_cond) / len(bene) * 100, 1),
        'avg_spend_with': round(with_cond['total_spend'].mean()),
        'avg_spend_without': round(without_cond['total_spend'].mean()),
        'median_spend_with': round(with_cond['total_spend'].median()),
        'median_spend_without': round(without_cond['total_spend'].median()),
    }
    row['spend_delta'] = row['avg_spend_with'] - row['avg_spend_without']

    other_conditions = (bene[CHRONIC_COLS] == 1).sum(axis=1) - has.astype(int)
    strata = (
        bene.assign(_has=has, _other=other_conditions)
        .groupby(['_other', '_has'])['total_spend']
        .agg(['mean', 'count'])
        .unstack('_has')
        .dropna()
    )
    weights = strata[('count', True)]
    gaps = strata[('mean', True)] - strata[('mean', False)]
    row['adjusted_spend_delta'] = round((gaps * weights).sum() / weights.sum())
    return row
