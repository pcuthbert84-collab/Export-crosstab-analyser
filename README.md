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
