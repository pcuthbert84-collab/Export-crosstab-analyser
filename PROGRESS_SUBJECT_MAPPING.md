# Progress subject mapping — Version 2.2

## Goal
Allow leaders to map baseline assessment subjects when subject names change between year groups, without altering attainment or CAT4 calculations.

## Example
- Upload Year 6 and Year 7 DCPro files using a consistent student identifier.
- Select preferred and fallback baseline/current assessment columns.
- Expand **Optional · Progress subject mapping**.
- Under `Year 7 English ← Year 6 subjects`, choose `Reading`, `Writing` or both.
- With both selected, the system averages available baseline grade points for each student. If only Reading is available, Reading is used; if neither is available, progress remains unavailable.
- The status panel displays how many student-subject outcomes were mapped and which comparisons require a separately approved conversion.

## Safeguards
- Applies only if a current subject has **no usable baseline** and **no existing comparable progress**.
- Matches student IDs exactly; never joins students by name, row position or fuzzy similarity.
- Does not overwrite an existing current-subject baseline.
- Does not alter attainment, targets, value added or raw grade data.
- Subject-to-subject matching is selected explicitly, never silently inferred.
- Grade conversion is conservative: only same grade kinds and approved KS3 ME->GCSE4 and ME+->GCSE6 equivalents are supported for cross-system averages.
- Mixed or unsupported grade conversions are flagged for review.
- Audit columns distinguish mapped baselines from original grades. Grade decline is not computed from a synthetic average.
- User mappings are active-session only. Use fictional/anonymised data on Streamlit Community Cloud; **not approved for identifiable student data**.

## Tests
Run `PYTHONPATH=. pytest -q` at the project root. Includes dedicated tests for single-subject, two-subject average, partial coverage, missing joins, existing baselines, approved cross-grade anchors and unsupported conversions.
