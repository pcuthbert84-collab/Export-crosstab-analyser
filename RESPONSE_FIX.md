# v2.5 — Responsive assessment view fix

**Reported issue:** Selecting Attainment versus Progress did not immediately update the displayed results.

**Change:** Removed eager `st.tabs` for the attainment/progress results table and used a horizontal `st.radio` selector. Streamlit reruns the script immediately when the selector changes and renders only the selected table, detail panel and download. The selection has a stable widget key.

**Performance:** Session-local keyed reuse for computed presentation summaries. The key includes every visible row's measure-defining fields and the grouping/method; it must invalidate when inputs or filters change. No shared Streamlit cache is used.

**Deployment check:** Open School Overview and Subject Analysis; alternate Attainment / Progress and Compact / Detailed and verify the heading, percentage columns, tables and downloaded filenames change immediately. Check different filters and check that changing the current assessment point invalidates the results.

**Production caveat:** Use synthetic or properly anonymised records on free Streamlit Community Cloud.
