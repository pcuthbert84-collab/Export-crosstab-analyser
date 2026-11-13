# Approved Science grade equivalences — DBSJP

**Approved by:** DBSJP assessment lead, 13 November 2026  
**Scope:** Progress calculation only, Science subjects using GCSE numeric or Combined Science paired GCSE grades.  
**NOT approved:** application to other subjects; general CAT4/target conversion; Value Added; automatic subject matching beyond existing subject transition library.

| KS3 Science descriptor | Numeric GCSE reference | Combined Science paired reference |
|---|---:|---|
| WT- | 1 | 1,1 |
| WT | 2 | 2,2 |
| WT+ | 3 | 3,3 |
| ME- | 3 | 3,3 |
| ME | 4 | 4,4 |
| ME+ | 6 | 6,6 |
| EX- | 7 | 7,7 |
| EX | 8 | 8,8 |
| MA | 9 | 9,9 |

The preceding Science descriptor is converted to the agreed GCSE reference. Current Combined Science `a,b` results are compared by the mean of their two components to the mean of the reference pair `n,n`. Existing **high-achievement policy** remains: GCSE 7+ and Combined Science 7,6+ are labelled Better even if they equal or fall below a descriptor's numeric equivalent. Thus `EX- -> 7` and `EX- -> 7,7` are labelled Better under *current school engine policy*, not Expected. This is a policy tension worth confirming with the assessment lead; it was deliberately **not silently changed** in this release. Other examples: `ME -> 4,4` Expected, `ME+ -> 6,6` Expected, `ME+ -> 6,5` Less.

The Science mappings already approved in `approved_subject_transitions.json` remain in place: Year 9 Science -> Year 10 Science - Combined/Biology/Chemistry/Physics; Year 7 Drama remains explicitly unmapped. Source/target grade parsing, optional session mapping and student matching remain as previously implemented.

## Private-source local audit (not included in distribution)

Using the local uploaded `Export Crosstab (83).xlsx` for Year 10 with **DP3 CPL / AG 2025/26** as the baseline and **DP1 CPL / AG 2026/27** as the current grade, `apply_same_cohort_mappings` yielded:

| Year 10 current subject | Valid current | Classified before | Classified after |
|---|---:|---:|---:|
| Science - Combined | 99 | 0 | 92 |
| Science - Biology | 17 | 0 | 17 |
| Science - Chemistry | 17 | 0 | 17 |
| Science - Physics | 17 | 0 | 17 |
| Total assessment records | 150 | 0 | 143 |

The 7 exclusions lack usable prior Science source grades; this does not indicate a failed grade conversion. Totals are assessment records and can include the same student in multiple different Science subjects. **No student records or source workbooks are included in this release.**

Run checks: `PYTHONPATH=. python -m pytest -q`.

## Remaining deployment checks

A full interactive Streamlit browser test is still required after redeploy. Test the default Year 10 automatic mapping toggle, year-10 filters, Data Quality/Progress Coverage summaries, and CSV/Excel exports against synthetic data before production use. Hosting remains *development-only* on Streamlit Community Cloud; do not upload student-identifiable data there without a school-approved compliant environment.
