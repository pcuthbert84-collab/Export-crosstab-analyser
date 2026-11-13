# DBSJP Data Intelligence v3.5 — GCSE to A Level progress

## Approved progress destinations (all A Level subjects)

| GCSE baseline | Expected A Level result |
|---|---|
| 1 | U |
| 2 | E |
| 3 | D |
| 4 | C |
| 5 | C |
| 6 | B |
| 7 | A |
| 8 | A |
| 9 | A* |

**Override:** current A or A* is always classified Better under the already-agreed A Level high-achievement exception, including all GCSE 7+ to A/A*. This overrides an exact destination match; thus GCSE 9 → A* is Better, and GCSE 8 → A is Better. Other current grades are classified Better/Expected/Less against the expected A Level grade. This deliberately creates unusual distributions and should be reviewed before high-stakes reporting.

**Scope:** all A Level subjects, not BTEC IT or other qualifications. A Level-to-A Level progress continues using the existing grade-scale comparison. This changes progress only, not attainment or grade-based VA/targets. GCSE U as baseline has no approved A Level destination and remains unclassified; A Level U as current result is valid and worth 0. N/A is missing and uses a configured fallback.

**Important setup:** For Year 12, choose `DP Exam Grade 2025/26` as the baseline assessment (or baseline fallback) and `DP1 CPL / AG 2026/27` as the current assessment. Both values are present within the same uploaded Year 12 DCPro workbook, although not every student has both. If a different baseline is selected, counts may change. For Year 13, comparing A Level baseline-to-current is unchanged.

## Actual supplied Year 12 Mathematics workbook audit (aggregate only)

- 34 current A Level Mathematics results; 31 have a matched GCSE exam-grade baseline and thus classified progress.
- 11 Better, 0 Expected, 20 Less (given the exact approved model and A/A* override).
- Source: the user's Export Crosstab (82) workbook. Only aggregate figures are recorded here; no student identifiers or assessment rows are included in the release.

## Verification

- `PYTHONPATH=. pytest -q`: 249 automated tests plus 6 subtests passed.
- Synthetic Year 12 records validated across A Level Mathematics, Physics, History, Psychology and English Literature; GCSE 1–9, high-grade override, same-cohort source matching, and unapproved GCSE U case.
- Live Streamlit browser interaction remains unverified.
- This ZIP contains synthetic records only. Do not upload identifiable data to free Streamlit Community Cloud.
