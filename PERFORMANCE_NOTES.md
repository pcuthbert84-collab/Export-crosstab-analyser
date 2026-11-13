# Performance update (v2.4)

## Symptoms and cause

Streamlit reruns the application after interactions with selectors and filters. Previously, every rerun decoded each uploaded `.xlsx` workbook, parsed every subject grade column, detected candidate subject mappings, recalculated grade classifications, and generated new calculated datasets before showing results. Repeated work becomes especially noticeable with multiple DCPro exports on free Community Cloud.

## Changes made

- Uploaded workbooks are read **once per uploaded file content per user session**, then reused during UI-only reruns.
- Parsed per-sheet records are reused if the workbook, worksheet and confirmed year are unchanged.
- Combined records, subject-mapping candidates, grade calculations and mapped progress outputs are reused unless their relevant inputs change.
- Each cache namespace holds only the latest result, preventing unbounded accumulation per session.
- `Clear uploads and analysis` resets the file uploader and discards the session-owned intermediate datasets.
- No `st.cache_data`, `st.cache_resource`, disk database or cross-user cache was added.

## Invalidation and limits

Changing a workbook, the selected sheets, the assigned year, assessment-column choices or subject-mapping rules triggers recalculation of the affected stages. Phase, year, subject, grade-focus and presentation filters reuse calculated grades; they still redraw tables and Plotly graphs.

This optimises repeated interactions, **not necessarily initial Excel upload speed**, which still requires reading and converting workbooks. Free Streamlit Community Cloud may also experience cold starts and limited CPU/RAM; neither can be eliminated within the app.

## Smoke tests and expected verification

Automated tests: `PYTHONPATH=. pytest -q` (58 tests and 6 subtests in this release).

Synthetic microbenchmark: 650 pupils x 10 subjects (6,500 subject results) yielded ~0.09 s fresh derivation and ~0.000004 s session reuse in the development environment. This only measures the calculation layer, not a hosted full-page response and is not a promise of end-user load time.

After deploying, verify that:
1. Uploads work and year groups are confirmed correctly.
2. Changing a graph/phase/subject filter keeps results correct and feels noticeably faster.
3. Changing assessment selection recomputes results.
4. Changing a transition mapping recomputes progress but not attainment.
5. Clearing uploads and analysis removes the files from the uploader and returns to the starting screen.

## Security

Session-only in-memory reuse is NOT sufficient to protect identifiable student information on public Streamlit Community Cloud. This remains a development prototype restricted to fictional or properly anonymised data until IT-approved hosting and role controls are in place.
