# DBSJP approved subject-transition library — governance

## Purpose
Rules describe which subjects from the previous year can be used as a baseline when the current subject has no directly comparable baseline. Only a **year and subject mapping** is saved in the repository, never student grades or identities.

## What is approved?
The file `approved_subject_transitions.json` ships with a **proposed** example, Year 6 Reading + Writing → Year 7 English. This is **not yet approved**. The dashboard may show it as a suggestion, but it never automatically applies it. Do not mistake a prototype's approval field for authenticated approval.

## Approval steps (outside the dashboard)
1. A teacher or assessment leader selects earlier-year source subjects in the dashboard, and optionally downloads the *non-personal* `DBSJP_Subject_Mapping_Proposals.json`.
2. The designated subject leader and school assessment lead verify curriculum comparability and the intended mean/single-source rule, documenting the rationale.
3. An authorised repository maintainer edits `approved_subject_transitions.json`. Set `status` to `approved` and include `approved_by` (named reviewer/title), `approved_on` (ISO YYYY-MM-DD date), and `rationale`. The `method` must be `single` for exactly one source, or `mean_available` for multiple sources.
4. Review that change in a pull request; ensure protected main branch or equivalent controlled workflow; run tests; deploy the reviewed revision.
5. If a rule becomes invalid, set `status` to `retired`, with a reason in the change review. Keep old changes in Git history for traceability.

## How it behaves
- Only **approved** rules with a matching target year/subject and *all source subject names present* in the uploaded earlier-year data are preselected and enabled in the mapping menu.
- Individual users may disable or change a mapping for their **current session**; overrides are not saved to the library and should be scrutinised before official reporting.
- Students must be matched on student ID across years. The mapping is applied only when a valid same-subject baseline is absent.
- For several sources, the calculation uses the arithmetic mean of the available valid converted grade points for that student, and records which sources were used. If none exists, progress is left blank.
- **Grade-scale equivalence is a distinct approval decision.** A subject mapping does not authorise new conversions or arbitrary comparisons; existing grade-conversion checks still apply.
- The site does not have authenticated administrators. Editing a JSON file in the GitHub repository is an administrative process, not permission enforcement. Do not use real student data on free Streamlit Community Cloud.

## Example approved entry
```json
{
  "from_year": 6,
  "to_year": 7,
  "current_subject": "English",
  "source_subjects": ["Reading", "Writing"],
  "method": "mean_available",
  "status": "approved",
  "approved_by": "[Reviewer / role]",
  "approved_on": "2026-11-13",
  "rationale": "[Evidence-based decision and subject-leader sign-off]"
}
```
Replace placeholder metadata only after genuine approval. Library validation prevents incomplete approved rules and duplicates.
