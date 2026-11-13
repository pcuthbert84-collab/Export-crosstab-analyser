# DBSJP Progress Audit — Phase 3 English

**Build:** 2.6. **Inputs audited:** 13 DCPro exports, Export Crosstab (80)–(92). **No student-level data is included in this report.**

## Verified Phase 3 English counts (before any optional same-cohort subject mapping)

| Year | Students with current English grade | Progress classified | Baseline missing | Baseline/current present but unclassified |
| --- | ---: | ---: | ---: | ---: |
| 7 | 159 | 0 | 159 | 0 |
| 8 | 152 | 81 | 13 | 58 |
| 9 | 124 | 70 | 12 | 42 |
| 10 | 130 | 65 | 7 | 58 |
| 11 | 138 | 0 | 138 | 0 |
| **Phase 3** | **703** | **216** | **329** | **158** |

The uploads contain 709 distinct students across Years 7–11, of whom 703 have a valid current English attainment grade. Hence the screenshot's 216 progress denominator reflects **classified comparisons**, not Phase 3 enrolment or English attainment coverage. 487 currently graded records are omitted from the progress denominator.

## Why the source data is not currently classified

* **Year 7:** The Year 7 export contains Year 7 English current grades and *Year 6* Reading/Writing DP3 grades under separate subject columns. They must be matched **within the Year 7 cohort**, not by matching to different students in a contemporary Year 6 workbook.
* **Year 11:** The Year 11 export contains English current DP1 grades and 138 English Language previous-exam grades under a different subject heading. If a school leader explicitly maps the source and confirms its appropriateness, those 138 can be compared using existing GCSE-grade rules. This raises eligible Phase 3 English progress from **216 to 354** in the audited files.
* **Years 8–10:** All 158 unclassified pairs have descriptor baseline grades and numeric current grades for which the engine does not yet have school-approved equivalence rules, e.g. EX-/EX/MA/ME-. It correctly does **not** guess a GCSE equivalent.

## What changed in v2.6

1. Added an **expanded-by-default Progress coverage** audit for School Overview, showing classified / unclassified / missing baseline counts for each subject and year.
2. Added a visible overall progress coverage reminder before graphs and tables.
3. Added an optional **Match previous grades within the same cohort export** selector. Multiple subject-year mappings may be enabled for the current session.
4. Mapping is by student ID and current enrolled year. Existing baselines/progress/attainment/targets are never overwritten. Missing or duplicate source grades do not become fabricated progress.
5. No unsupported grade equivalence is silently inferred. Approval of subject mappings remains separate from approval of numerical grade conversion rules.

## Recommended checking procedure

1. Upload all 13 year-group exports and confirm their detected years.
2. Set baseline first choice to `DP3 CPL / AG 2025/26`, optional baseline fallback to `DP Exam Grade 2025/26`, and current first choice to `DP1 CPL / AG 2026/27`.
3. Filter to Phase 3 and inspect the Progress coverage panel. Check Year 7/11 English exclusions.
4. If pedagogically approved, open the optional same-cohort mapping panel and select **Year 11 English ← English Language**. Verify the mapped-result count and coverage increase.
5. Consider **Year 7 English ← Reading and Writing**. The system will still exclude unsupported descriptor-to-GCSE conversions. Confirm a complete conversion policy before treating Phase 3 progress headline percentages as representative.
6. When checking scores, compare current-grade coverage separately from progress eligibility and use caution with judgements based on low coverage.

**Data protection:** The original Excel files contain actual student information. Do not upload them to the free Community Cloud prototype. Keep them within approved school systems pending IT approval. The project ZIP contains no copies of the uploaded real-data spreadsheets or their student-level records.
