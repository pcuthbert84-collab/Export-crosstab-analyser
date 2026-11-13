# Version 3.4 — Approved BTEC IT grade conversion

## Approved scope

**Only** Year 10 BTEC IT (and other explicitly named BTEC IT records in the same approved subject pathway) receives the prior ICT descriptor → BTEC qualification grade conversion. The existing Year 9 ICT → Year 10 BTEC IT subject mapping remains in `approved_subject_transitions.json` and is not changed.

| Prior ICT descriptor | Expected BTEC IT grade |
|---|---|
| WT-, WT, WT+, ME- | Fail |
| ME | Pass |
| ME+ | Merit |
| EX-, EX | Distinction |
| MA | Distinction* |

Progress uses the BTEC qualification ordering **U < Fail < Pass < Merit < Distinction < Distinction***: equal grade is Expected, higher is Better, lower is Less. This cross-qualification rule is NOT enabled for other BTECs or subjects. Existing direct BTEC-to-BTEC comparisons remain unchanged. It does not modify attainment, targets or value added.

## Year 10 DCPro source audit (aggregate only)

Checked against the supplied `Export Crosstab (83).xlsx` (not distributed). Baseline: `ICT, DP3 CPL / AG 2025/26`; current: `BTEC IT, DP1 CPL / AG 2026/27`. Student IDs are matched within the same cohort workbook. All 25 current BTEC IT grade records have valid prior ICT grades. With the approved subject and conversion mapping, **25/25** have progress: **14 Better, 7 Expected, 4 Less**. No real student data is in this release.

## Tests

`PYTHONPATH=. pytest -q` yielded **224 passed, 6 subtests passed**. Tests cover all descriptor equivalences, the ordered BTEC comparison, high/low cases, subject scoping, within-cohort mapping, non-regression of same-kind BTEC progress and preservation of previously approved mappings. The Streamlit browser UI is not end-to-end tested in this environment.

## Deployment

Replace the prior repository's application files with this ZIP's contents at repository root (preserve `.streamlit/`). `btec_it_grade_conversions.py` must sit alongside `engine.py` and `progress_subject_mapping.py`.

**Security:** free Streamlit Community Cloud must be used only with synthetic or properly anonymised DCPro data until approved hosting and permissions are implemented.
