# v3.3 — Approved subject decisions

- Year 10 Business / Psychology: no Year 9 mapping; report within-course progress only where two valid comparable grades exist in the same workbook. Does **not** auto-create baselines when DP3 is blank.
- Year 10 Design Technology ← Year 9 Technology (same cohort prior-assessment column).
- Year 10 BTEC IT ← Year 9 ICT (subject approval only; ICT descriptor to BTEC grades is **not** an approved qualification conversion, so progress may remain unclassified).
- Year 10 Computer Science ← Year 9 ICT.
- Year 7 French / Spanish: use their own previous subject grade if available (already the direct calculation engine behavior). Missing stays missing.
- Year 11 Triple Science ← available Year 10 Biology, Chemistry and Physics grades using a mean of their **approved comparable grade points**. One current Triple Science assessment result is produced; no duplicate students.
- Year 12 Mathematics: source GCSE Mathematics exam grade exists but GCSE-to-A-Level progress conversion has not been specified or approved. Kept pending, no numerical grade conversion added.
- Year 11 History reverse conversion remains pending.
- Primary missing baseline grades remain unclassified.

Implementation note: this release does not alter `engine.py`, `grade_equivalences.py` or any previously approved transitions. School-hosting approval is required before using identifiable records.

## Aggregate check against supplied DCPro column structures (not included in release)

Same-cohort mapping with DP3 2025/26 baseline, previous exam fallback, and DP1 2026/27 current:

| Cohort | Subject | Current valid | Progress classified | New mapped results |
|---|---|---:|---:|---:|
| Year 7 | French | 158 | 81 | 0 (direct prior French grades) |
| Year 7 | Spanish | 158 | 70 | 0 (direct prior Spanish grades) |
| Year 10 | Business | 99 | 0 | 0 (no first course baseline in selected assessment) |
| Year 10 | Psychology | 47 | 0 | 0 (no first course baseline in selected assessment) |
| Year 10 | Design Technology | 28 | 26 | 26 |
| Year 10 | BTEC IT | 25 | 0 | 0 (25 source grades found, conversion not approved) |
| Year 10 | Computer Science | 23 | 20 | 20 |
| Year 11 | Triple Science | 22 | 22 | 22 |
| Year 12 | Mathematics | 34 | 0 | 0 (GCSE-to-A-Level comparison pending conversion policy) |

The seven previous approved rules remain unchanged. Across Year 10, DT/Computer Science use universal descriptor-to-GCSE conversion where applicable; BTEC remains blocked rather than using a guessed descriptor-to-BTEC comparison.

Note: Year 12 GCSE Mathematics grades are in the same workbook under `DP Exam Grade 2025/26`; A Level DP1 grades are letters. The source subject identity is established, but no approved numerical GCSE-to-A-Level *progress* destination rule exists yet. The requested 'with approved A Level conversion' condition is **not met** and no new conversion was silently added.

Future refinement: Separate 'Within-course progress' from 'Prior-year progress' explicitly in subject-level summaries and PPM exports; currently the policy is attached to the calculated records and viewable as an aggregate policy panel.
