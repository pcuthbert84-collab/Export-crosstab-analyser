# DBSJP Data Intelligence — Leadership Dashboard v2.0

A Streamlit development prototype for **subject analysis, school/phase overview, progress and attainment, KHDA-style judgements, PPM student discussions, group comparisons and grade-based target measures**.

## IMPORTANT — NOT APPROVED FOR IDENTIFIABLE STUDENT DATA

This is a **development prototype for synthetic or properly anonymised records**. It does **not** have school-approved hosting, Microsoft Entra ID authentication, role-based permissions, production data lifecycle controls, independent security testing, or regulatory/privacy sign-off. Do not upload live or identifiable student records to a publicly hosted instance. It is not production-ready.

## Deployment to Streamlit Community Cloud (fictional data only)

1. Create a new GitHub repository for the prototype. Do not upload real student exports, historical Data Packs containing student data, personal secrets or credentials.
2. Extract the ZIP and upload `app.py`, `engine.py`, `overview_tables.py`, `dashboard_analytics.py`, `dashboard_ui.py`, `dashboard_exports.py`, `requirements.txt`, and `.streamlit/config.toml` to the repository root, preserving the `.streamlit` folder.
3. Create a Streamlit app referencing the repo and set **Main file path** to `app.py`.
4. Upload the supplied **SYNTHETIC_DCPro_Year8.xlsx** file to check the interface.
5. Confirm the year group, baseline, current grade and target columns. Open the sidebar modules.

Locally, once dependencies can be installed:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Quick guide

- **School Overview:** uploaded-population KPI cards, comparative subject chart, KHDA judgement mix, descriptive findings, and Attainment / Progress tabs.
- **Subject Analysis:** subject-year, category-year and year-subject comparisons; chart; compact/detailed tables; individual-subject grade distribution.
- **PPM & Interventions:** concern counts, subject hotspots, multi-subject student priorities, student evidence drill-down and Excel exports.
- **Student Groups:** group-by-subject comparison charts, full-row judgement colours and Excel download.
- **Value Added & CAT4:** target pair counts, target achievement rates and actual-minus-target differences.
- **Exam Results:** clearly identified as a future public-exam import, not an invented result from DP grades.
- **Reports & Data Pack:** aggregate PDF and Excel exports only. The 87-table historical Data Pack is **not yet implemented**.
- **Filters:** expandable phase / year / reporting subject / individual subject / group, with year options restricted by phase. Phase 1 processing is deferred.

## KHDA-style colour legend

| Judgement | Colour |
|---|---|
| Outstanding | Blue |
| Very Good | Green |
| Good | Yellow |
| Acceptable | Orange |
| Weak | Red |

Rows without a valid judgement have no status colour. Only eligible grades contribute to a calculation; denominators differ by measure.

## Tests and review log

See [IMPROVEMENT_CYCLES.md](IMPROVEMENT_CYCLES.md) for the **ten distinct review-and-improvement cycles** and validation outcomes.

To run verification tests:

```bash
PYTHONPATH=. python -m pytest -q
python -m py_compile app.py dashboard_ui.py dashboard_analytics.py dashboard_exports.py engine.py overview_tables.py
```

The final local run passed **31 Python tests**, plus 6 subtests, and an end-to-end **synthetic calculation/export smoke test**. Browser-level Streamlit validation is **still outstanding**, because Streamlit was unavailable in the test container and could not be installed from the package index. Validate the rendered UI on the deployed test app before considering acceptance.

## Important calculation and scope caveats

- Only uploaded year groups are represented; partial uploads must never be labelled complete whole-school outcomes.
- Combined-subject percentages use valid assessment records. The visible `Number` is unique students with eligible grades. For English, a valid generic English grade supersedes Reading/Writing for combined analysis.
- The KHDA-style system uses **whole-number, half-up rounded percentages**, with a minimum of 5 valid assessment results before showing a judgement; these are **calculated DBSJP indicators, not official KHDA judgements**.
- The progress exception **KS3 ME → GCSE 4 = Expected** is explicitly supported. Other cross-grade-set conversions remain provisional until approved.
- Standard target and challenge target measures have separate eligible denominators; missing values do not turn into zeros.
- Grade-based value added is a difference from target, *not* a statistically adjusted value-added measure.
- The current PDF is an assessment summary, **not** the final Data Pack.

## Production security work required before live use

School-approved hosting and data region; Entra sign-in with MFA; server-side role and subject/year/class permissions; download restrictions; safe audit logs; per-session memory isolation; upload malware/content scanning and limits; deletion testing; privacy impact assessment; independent penetration/security assessment; school approval.

### Version 2.1 — Year-group confirmation improvements

- Each uploaded workbook's year-group confirmation panel now opens by default.
- The app suggests the enrolled year from recurring DCPro subject-class codes (e.g., `8JPT`, `11A`, `12I`), then from a dedicated Year Group column or clear file/sheet name.
- It deliberately does **not** infer the enrolled year from curriculum grade prefixes or an academic-year label such as `2026/27`.
- Ambiguous or unknown years require manual selection, rather than silently defaulting to Year 8.
- Users can still override the suggestion. Every workbook should contain only one enrolled year group.
- The main phase/year/subject filter panel also opens by default.
- All existing assessment calculations, subject and PPM views remain unchanged.

## Version 2.2 — optional cross-subject progress mapping

In **Optional · Progress subject mapping** (after assessment-point selection), select the previous-year subject or subjects that form the baseline for a current-year subject. For example, upload Year 6 and Year 7 DCPro files with **consistent student IDs**, then select **Year 7 English ← Year 6 Reading, Writing**. Select one source to use its grade, or multiple sources to average the *available valid comparable grades for each student*. The app reports the source subjects used and the number of mapped comparisons.

This is **progress only**: the mapping does not alter current attainment, target achievement, value added, or the original Reading/Writing tables. Existing comparable progress and existing current-subject baselines remain untouched. The mapping is selected afresh during the active session; no permanent student data or cross-subject rule is stored. Unsupported cross-system conversions are shown in a review panel, not guessed. For approved KS3-to-GCSE transitions, ME maps to GCSE grade 4 and ME+ to grade 6. Students must match by student ID across uploaded year groups; files without reliable shared IDs cannot safely be joined.

Current limitation: the optional mapper uses the **immediately preceding enrolled year** and the selected baseline priority/fallback fields. When some of the selected source grades are absent, it averages those that are available and auditable. More complex multi-year or manually weighted mappings need a later release and documented school agreement.

## Approved subject-transition library (v2.3)

A repository-managed `approved_subject_transitions.json` provides repeatable, reviewed year-to-year subject mappings for progress. The initial Year 6 Reading + Writing → Year 7 English rule is **proposed**, not approved; a designated assessment/subject leader must authorise it before it can be preselected. Approved rules appear automatically when both years and all source subjects are present. Staff can override them for the current session without changing the official library. See `APPROVAL_WORKFLOW.md` for approvals, deployment and cautions. Grade-scale equivalence requires separate approval.

## Version 2.3 — reviewed transition mapping library

`approved_subject_transitions.json` is a non-personal, version-controlled library. Its initial Year 6 Reading + Writing → Year 7 English example is **proposed**, not automatically approved. Once genuinely signed off by a school reviewer, set it to `approved` and add reviewer/date/rationale via a reviewed GitHub update; only then will the Streamlit mapping menu preselect it. Users can still disable or override the selection for the current session. Full directions and safeguards are in `APPROVAL_WORKFLOW.md`.
