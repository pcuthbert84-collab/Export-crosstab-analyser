# English-only grade conversion approval — v3.1

Approved by the DBSJP assessment lead (user instruction), 13 November 2026.

| Earlier descriptor | GCSE English numeric equivalent |
|---|---:|
| WT- | 1 |
| WT | 2 |
| WT+ | 3 |
| ME- | 3 |
| ME | 4 |
| ME+ | 6 |
| EX- | 7 |
| EX | 8 |
| MA | 9 |

## Strict scope
- English progress comparisons only, including current English, English Language and English Literature when numeric GCSE grades are recorded.
- Existing approved Year 7 English ← mean of available Year 6 Reading and Writing grades (stored in Year 7 cohort export).
- Existing approved Year 11 English ← prior English Language (stored in Year 11 cohort export).
- Year 7 Reading/Writing mean is calculated on their **approved GCSE-equivalent points**; e.g. ME (4), ME+ (6) → 5.
- Other subjects, attainment, CAT4 target measures and value added are unchanged. Science retains its separate conversion approval.
- Existing high-achievement override of current GCSE 7+ → Better remains intact, including exact-equivalence EX-/7, EX/8, MA/9; this is a previously agreed policy requiring separate review if you want exact matches to be Expected.
- Subject relationships are governed separately by `approved_subject_transitions.json`.

## Coverage audit handling
- A selected mapped source grade that exists but has an unapproved conversion is counted under **Grade conversion not approved**, not **Current grade, baseline missing**.
- There is no need to retain source grades in the exported aggregate coverage sheet.
- Status is kept within the current processing session, not written to a database.

## Real DCPro QA
Using exports 80–92, selected baseline `DP3 CPL / AG 2025/26`, baseline fallback `DP Exam Grade 2025/26`, current `DP1 CPL / AG 2026/27`, and approved same-cohort mappings:

| Year | Current English grade results | v3.0 classified | v3.1 classified |
|---|---:|---:|---:|
| 7 | 159 | 36 | 152 |
| 8 | 152 | 81 | 139 |
| 9 | 124 | 70 | 112 |
| 10 | 130 | 65 | 123 |
| 11 | 138 | 138 | 138 |
| **Total** | **703** | **390** | **664** |

Still 39 results without a usable baseline: Y7=7, Y8=13, Y9=12, Y10=7. These are based on that exact configuration and files, not a guarantee for other uploads or assessment selections. No real student data is included in this release.

Tests cover direct progress, cross-year mapping, same-cohort mapping, scope controls, baseline preservation, missing versus unsupported source diagnostics and single/paired-grade safeguards. Run `PYTHONPATH=. pytest -q`.

**Deployment:** Streamlit Community Cloud remains unsuitable for identifiable student records until DBSJP/Taaleem security approval. Live browser verification still required.
