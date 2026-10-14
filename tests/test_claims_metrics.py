import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.claims_metrics import (
    CHRONIC_COLS,
    READMIT_FLAG_SQL,
    STAYS_FLAGGED_CTE,
    attach_conditions,
    condition_impact,
    flag_readmissions,
    load_inpatient_stays,
    spending_tier,
)

# (patient, claim, admit, discharge) -> expected readmitted_30d on that stay
STAYS = [
    ('A', 1, 20080101, 20080105, True),    # next admit 30 days after discharge
    ('A', 2, 20080204, 20080210, False),   # next admit 31 days after discharge
    ('A', 3, 20080312, 20080315, False),   # last stay
    ('B', 4, 20090601, 20090610, False),   # same-day transfer (0 days)
    ('B', 5, 20090610, 20090620, False),   # overlaps the next stay
    ('B', 6, 20090615, 20090618, True),    # next admit 1 day after discharge
    ('B', 7, 20090619, 20090625, False),
    ('C', 8, 20081230, 20081231, True),    # crosses a year boundary
    ('C', 9, 20090102, 20090103, False),
    ('D', 10, 20080103, 20080104, False),  # different patient, never readmitted
]


def stays_frame():
    df = pd.DataFrame(
        [s[:4] for s in STAYS],
        columns=['DESYNPUF_ID', 'CLM_ID', 'CLM_ADMSN_DT', 'NCH_BENE_DSCHRG_DT'],
    )
    df['CLM_DRG_CD'] = '001'
    df['ICD9_DGNS_CD_1'] = '486'
    df['CLM_PMT_AMT'] = 1000.0
    return df


def expected_flags():
    return {s[1]: s[4] for s in STAYS}


def test_flag_readmissions_window_edges():
    flagged = flag_readmissions(stays_frame().sample(frac=1, random_state=0))
    assert dict(zip(flagged['CLM_ID'], flagged['readmitted_30d'])) == expected_flags()


def test_flag_readmissions_keeps_one_row_per_stay():
    assert len(flag_readmissions(stays_frame())) == len(STAYS)


def test_flag_readmissions_rejects_duplicate_claims():
    df = pd.concat([stays_frame(), stays_frame().head(1)])
    with pytest.raises(ValueError):
        flag_readmissions(df)


def test_sql_and_pandas_readmission_logic_agree():
    conn = sqlite3.connect(':memory:')
    df = stays_frame()
    df['SEGMENT'] = 1
    # a second segment of claim 1 must not count as another stay
    extra = df.head(1).assign(SEGMENT=2, CLM_DRG_CD='OTH')
    pd.concat([df, extra]).to_sql('inpatient_claims', conn, index=False)

    sql = pd.read_sql(
        STAYS_FLAGGED_CTE + f"SELECT CLM_ID, {READMIT_FLAG_SQL} AS readmitted FROM flagged", conn
    )
    assert len(sql) == len(STAYS)
    assert {k: bool(v) for k, v in zip(sql['CLM_ID'], sql['readmitted'])} == expected_flags()

    pandas_flags = flag_readmissions(load_inpatient_stays(conn))
    assert pandas_flags['readmitted_30d'].sum() == sql['readmitted'].sum()


def test_attach_conditions_does_not_duplicate_stays():
    flagged = flag_readmissions(stays_frame())
    bene = pd.DataFrame(
        [(p, y, 1 if y == 2009 else 2) for p in 'ABCD' for y in (2008, 2009, 2010)],
        columns=['DESYNPUF_ID', 'YEAR', 'SP_CHF'],
    )
    merged = attach_conditions(flagged, bene)
    assert len(merged) == len(flagged)
    # flag comes from the admission year, not any year
    assert merged.loc[merged['CLM_ID'] == 8, 'SP_CHF'].item() == 2
    assert merged.loc[merged['CLM_ID'] == 9, 'SP_CHF'].item() == 1


def test_spending_tier_covers_every_row():
    spend = pd.Series([-50, 0, 0.01, 500, 500.01, 2000, 5000, 10000, 10000.01, 400000])
    tiers = spending_tier(spend)
    assert tiers.notna().all()
    assert list(tiers) == [
        'No spend', 'No spend', '$0-500', '$0-500', '$500-2K',
        '$500-2K', '$2K-5K', '$5K-10K', '$10K+', '$10K+',
    ]


def test_adjusted_delta_removes_comorbidity_confounding():
    # CHF adds exactly 1,000; every *other* condition adds 5,000. CHF patients
    # carry more other conditions, so the raw delta overstates CHF's effect.
    rows = []
    for has_chf, n_other, n in [(1, 0, 10), (1, 2, 90), (2, 0, 90), (2, 2, 10)]:
        for _ in range(n):
            row = {c: 2 for c in CHRONIC_COLS}
            row['SP_CHF'] = has_chf
            for c in [c for c in CHRONIC_COLS if c != 'SP_CHF'][:n_other]:
                row[c] = 1
            row['total_spend'] = 1000 * (has_chf == 1) + 5000 * n_other
            rows.append(row)
    result = condition_impact(pd.DataFrame(rows), 'SP_CHF')

    assert result['spend_delta'] == 9000
    assert result['adjusted_spend_delta'] == 1000
