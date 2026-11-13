# Version 2.6 — Progress denominator audit and same-cohort subject matching

New files: `same_cohort_mapping.py`, `progress_coverage.py`, `PROGRESS_AUDIT_FINDINGS.md`, and `tests/test_same_cohort_mapping.py`.

The uploaded data identified an important design gap: *previous-year* DP3/Exam results can be under a different subject **inside the current year-group export**. They must be matched to a student's current grade within the same cohort, rather than to a different current-year group.

The prototype now presents explicit coverage/exclusion counts and lets the user make these subject mappings selectively. It does not auto-approve grade conversions. This is a classification and transparency fix, not a claim that all missing progress can now be calculated.

To update GitHub: unzip the package, replace `app.py` and all existing application modules, add `same_cohort_mapping.py` and `progress_coverage.py`, commit, and allow Streamlit to redeploy. `app.py` remains the Streamlit entry point.

Validation: 65 automated Python tests and six subtests passed; local reproducibility audit matched the 216-student screenshot denominator and verified that approved-style Year 11 English Language mapping adds 138 progress results. **The live hosted browser has not been tested**, and none of these changes constitutes approval to process identifiable data on free Streamlit Community Cloud.
