# Version 3.1 — English progress and coverage fix

- Adds `english_grade_conversions.py` with nine school-approved English-only descriptor-to-GCSE equivalences.
- Applies the conversion to direct English results and both optional mapping paths.
- Retains all pre-approved subject transitions without altering JSON rules.
- Corrects coverage reporting for source grades present under a mapped subject but blocked by conversion approval.
- No new grade equivalences are enabled for Mathematics or other non-English subjects.
- Source audit against uploads 80–92: 390 → 664 valid Phase 3 English comparisons out of 703 current English grade results.
- Does not address the 39 English results with no usable baseline.
- Python unit tests and integration checks required; browser UI not tested here.
- Do not upload identifiable student data to free Streamlit Community Cloud.
