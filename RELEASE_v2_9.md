# DBSJP Data Intelligence v2.9 — Drama and Science mapping decisions

## Approved decisions (2026-11-13)

- **Year 7 Drama:** intentionally **unmapped** (Y6 → Y7). No automatic suggested source is used, and existing valid same-subject baselines are not suppressed.
- **Year 10 Combined Science:** Y9 `Science` → Y10 `Science - Combined`.
- **Year 10 Biology:** Y9 `Science` → Y10 `Science - Biology`.
- **Year 10 Chemistry:** Y9 `Science` → Y10 `Science - Chemistry`.
- **Year 10 Physics:** Y9 `Science` → Y10 `Science - Physics`.

All four Science rules use **same-cohort prior assessment**: the previous academic year's Science grade is recorded in the enrolled Year 10 export, rather than copied from a different cohort's current Year 9 workbook. Each target is one current subject record; baseline reuse does not add student rows. Valid existing baselines and progress are never overwritten.

## Actual uploaded DCPro source-column verification

Verified locally using `Export Crosstab (83).xlsx` (Year 10):

- Source: `Science, DP3 CPL / AG 2025/26` (123 grades)
- Current `Science - Combined, DP1 CPL / AG 2026/27` (99 current grades; 92 matching source-grade records)
- Current `Science - Biology, DP1 CPL / AG 2026/27` (17 grades; 17 matching source-grade records)
- Current `Science - Chemistry, DP1 CPL / AG 2026/27` (17 grades; 17 matching source-grade records)
- Current `Science - Physics, DP1 CPL / AG 2026/27` (17 grades; 17 matching source-grade records)

The Year 7 export (`Export Crosstab (86).xlsx`) contains current Drama grades but no previous-year Drama grade, supporting the no-mapping decision.

**Grade conversion NOT approved or changed.** Under existing rules, the actual Year 10 export contains 143 mapped Science subject results requiring separate grade equivalence approval. Seven Combined Science current records have no usable selected Science baseline. This is a *mapping-only* approval and must not inflate progress denominators or percentages. In particular, descriptor → paired GCSE grades must not use an invented numeric mean or conversion.

## Verification

- `PYTHONPATH=. pytest -q`: 72 tests and 6 subtests passed.
- Real-file audit ran locally, but **no uploaded identifiable data is included in this ZIP**.
- Streamlit browser deployment and interactive verification remain outstanding.

## Deployment

Replace all application files from the ZIP in the existing GitHub repository, including `approved_subject_transitions.json` and `transition_library.py`. Approved mapping selections are automatically proposed and preselected when the relevant source grade columns are present; users can disable them for the current session. The application must only be tested using synthetic or properly anonymised data on Streamlit Community Cloud.
