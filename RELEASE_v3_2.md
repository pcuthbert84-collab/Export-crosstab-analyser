# DBSJP Data Intelligence v3.2 — Global Grade Equivalence and Fallback Rules

## Approved policy (13 November 2026)

Universal descriptor-to-GCSE equivalents for **all subjects** in progress calculations:

| Descriptor | GCSE equivalent | Paired GCSE reference |
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

- Applies to **all subjects**, including mapped subjects, when comparing descriptor baselines with numeric GCSE grades or legitimate paired GCSE grades.
- Both the baseline and current assessment columns normally come from the **same DCPro year-group workbook**; no separate previous cohort export is necessary for this conversion.
- `U` is a valid grade with numeric point **0** in GCSE, A Level and BTEC contexts. It is retained as the first-choice assessment grade, not treated as missing.
- `N/A` (case/whitespace insensitive), empty grade or unrecognised first-choice grade is skipped, and the user-selected fallback assessment column is checked. The system never substitutes a better grade simply because it is higher.
- An approved subject transition remains necessary when subject headings differ (e.g., prior Reading and Writing -> current English). Universal grade conversions do not invent a subject match.
- The existing high-grade progress override (numeric GCSE 7+ and paired >=7,6) is retained as previously approved. Thus a reference EX- -> 7 still counts as Better; consider a separate policy review of this exception.
- This equivalence is for cross-grade-set **progress** comparisons; descriptor attainment thresholds, within-descriptor progression, targets and Value Added keep their established separate semantics.
- Other unapproved qualification-to-qualification conversions (such as unrelated BTEC -> GCSE, A level -> GCSE) remain unsupported.

## Tests and evidence

- **198 automated tests plus six subtests** passed in the supplied test suite (run with `PYTHONPATH=. pytest -q`).
- Added end-to-end synthetic XLSX import that exercises preferred/fallback grade selection, `N/A` and valid `U` on the same sheet.
- Test for BTEC `U` being zero and Below standard.
- All 17 available DCPro-format workbook structures (Exports 76–92) were inspected for intake compatibility, without copying student data to this release. Observed 43 literal `U` cells in the uploaded source exports; the import code now processes these as zero.
- A live deployed Streamlit UI browser smoke test is still needed after deployment.

## Security

Use only synthetic or appropriately anonymised records on the free Streamlit Community Cloud prototype. The bundle contains only `SYNTHETIC_DCPro_Year8.xlsx` and code/tests, not real DCPro exports.
