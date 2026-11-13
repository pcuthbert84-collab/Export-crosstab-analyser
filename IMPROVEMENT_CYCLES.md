# DBSJP Dashboard — 10 completed review/improvement cycles

Each cycle involved making a code change and rerunning the local Python verification suite. The final suite covers calculations, table formatting, chart construction, exports and data handling. Streamlit browser rendering was **not** tested in this environment.

| Pass | Finding in review | Improvement implemented | Validation |
|---:|---|---|---|
| 1 | Existing headline KPIs could imply whole-school figures even for partial uploads | Added dedicated uploaded-cohort aggregate calculations, cautious coverage labels and PPM distinct-student counting | Cohort weighted/unweighted, cohort coverage and PPM test cases |
| 2 | Default UI looked like a technical data table; charts and colour presentation were inconsistent | Created reusable DBSJP visual theme, full-row KHDA judgement styling, comparison bars and judgement distribution chart | Chart-construction and colour-application tests |
| 3 | Users had to work through dense upload/configuration and tables | Rebuilt Streamlit app with clear leadership homepage, modules, 4 KPI cards, chart-first overview and concise tables | Python syntax and existing engine/table tests |
| 4 | PPM rows did not let leaders inspect one student's relevant assessment evidence | Added single-student subject evidence drill-down with baseline/current source columns | Python regression suite |
| 5 | Leaders needed to see the shape of grade outcomes, not only percentages | Added selectable subject/year grade-distribution chart | Grade-distribution chart test |
| 6 | Users could not focus tables on weaker or stronger judgements quickly | Added focus modes: all, Weak/Acceptable, Good+, or no judgement; exports follow filter | Judgement-focus tests |
| 7 | Source coverage and fallback usage were invisible | Added compact data-quality/source-coverage expander, fallback counts and duplicate warnings | Assessment coverage tests |
| 8 | Multi-subject PPM priorities did not show where concerns were concentrated | Added per-subject distinct-student hotspot chart without additive risk scores | Unique-student subject hotspot test |
| 9 | Reports and file formatting were difficult to maintain or independently test | Extracted in-memory styled Excel and aggregate PDF functions into separate tested module | Openpyxl workbook colour/header test and PDF integrity test |
| 10 | Default subject charts privileged high performers rather than areas needing attention | Added weakest-first / highest-first chart options, defaulting to areas requiring attention | Chart ranking tests |

### Final QA snapshot

- 31 passed automated Python test cases and 6 subtests.
- End-to-end synthetic workbook smoke test: parsed DCPro sample; derived outcomes; generated pooled English and Maths summaries; built both compact tables; generated charts; produced Excel and PDF bytes; checked PPM and source counts.
- No live Streamlit browser testing was possible here (Streamlit package absent and external package index unreachable). Actual runtime/UI compatibility must be tested in the deployed development app.
- Security controls are NOT production-ready. Use synthetic/fully anonymised datasets only.
