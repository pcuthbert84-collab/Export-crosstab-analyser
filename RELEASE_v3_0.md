# DBSJP Data Intelligence v3.0 — Science-only grade equivalences

- Added version-controlled `science_grade_conversions.py`, covering all 9 school-approved WT- through MA descriptor equivalences for numeric GCSE and paired Combined Science grades, **only for Science subjects**.
- Hooked conversion into direct `engine.progress`, optional previous-year-file mapping, and approved same-cohort source-subject mapping.
- Did not modify attainment, CAT4 target met, challenge target met, Value Added or any non-Science grade conversion rules.
- Retained all approved mappings in `approved_subject_transitions.json`, including Year 9 Science -> Year 10 Combined Science, Biology, Chemistry and Physics; Year 7 Drama stays unmapped.
- Added regression tests for all descriptor values, several double-GCSE pairs, no cross-subject leakage, the existing mappings, direct Science records, and no additional records created.
- Local source-column validation with the supplied Year 10 export classified 143 of 150 current Science subject assessments, up from 0. Seven had no usable prior Science source grade. No private data is included in the ZIP.
- **Interpretation caveat:** Existing high-achievement override classifies GCSE 7+ and Combined Science 7,6+ as Better, even where a descriptor conversion yields the same expected grade. Explicitly flagged for school policy review in `SCIENCE_GRADE_CONVERSION_APPROVAL.md`.
- Full Streamlit browser deployment not run in this environment. Use only synthetic/anonymised data on free Streamlit Community Cloud.
