# DBSJP Data Intelligence — V1 development prototype

A Streamlit prototype for DCPro Excel crosstab uploads, subject attainment and progress, combined categories, PPM intervention lists, student-group analysis, CAT4 target achievement, value added and basic downloadable summaries.

## Getting started locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy to GitHub and Streamlit Community Cloud (synthetic data only)

1. Create a new GitHub repository (preferably private).
2. Upload `app.py`, `engine.py` and `requirements.txt` at the repository root.
3. In Streamlit Community Cloud, create an app from the repository. Set the entrypoint/main file to `app.py`.
4. Open the deployed app. Upload **synthetic or properly anonymised** DCPro spreadsheet exports, confirm each year group and select preferred/fallback assessment columns.

**Do not deploy with identifiable student records or real school data on Community Cloud without institutional approval, a security/privacy review, Microsoft 365 sign-in, role-based permissions, appropriate hosting and retention controls.** This V1 does not implement those protections.

## Features included

- Multiple DCPro `.xlsx` files, optional workbook-sheet selection, manual year-group confirmation.
- Current and baseline assessment selections with one fallback each, plus target/challenge target selections.
- Grade parsing: GCSE 1–9/U, KS3 descriptors, BTEC labels, double GCSE pairs, and limited A Level cases.
- Individual subject, combined-category, year-group and student-group breakdowns.
- English deduplication: generic English supersedes Reading/Writing for combined headlines.
- Attainment, progress and DBSJP KHDA-style judgements; CAT4 target achievement and grade-based value added.
- PPM concern tables and Excel exports; basic PDF summary.

## Important limitations

1. **Not production-ready for personal information.** No Microsoft 365 login, authorization or secure production hosting. The application does not intentionally save uploaded student data, but upstream hosting, caching and downloads require a privacy assessment.
2. No EYFS, NGRT, GL/IBT/external importers, historical Data Pack matching, full 87-table PDF generator or public examination results import yet.
3. Grade conversion map remains provisional for A Level, BTEC, year-prefixed descriptor transitions and other cross-qualification comparisons. Unsupported progress is blank rather than guessed. Crucially, KS3 ME → GCSE 4 is approved as expected progress.
4. The subject/year allocations and comparisons must be validated against synthetic fixtures and user-approved mapping rules. Where both source and fallback have a grade, first priority always wins.
5. One grade column selection is made across subjects; absent columns are ignored. Different exports may have different assessment headers. Source matching will be expanded later.
6. Historical or incomplete phase/whole-school data is not represented as a complete school population.

## Test locally

```bash
python -m unittest discover -s tests -v
```

## Version 2 roadmap

- Official assessment-column mapping wizard by subject and year.
- Complete conversion-review UI and approved grade mappings.
- Public examination grade distribution/cumulative thresholds with qualification detection.
- Data Pack PDF based on the uploaded 2025–26 87-table Word template, historical pack import, blank-table export toggle.
- Optional EYFS and external tests including NGRT.
- Microsoft Entra ID / Microsoft 365 authentication, role-based access, school-approved deployment and compliance review.
