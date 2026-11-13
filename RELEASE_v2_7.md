# v2.7 — Approved subject transitions

Changes: two user-confirmed English transition rules approved in `approved_subject_transitions.json`; explicit `source_scope` discriminator added to library validation and lookup; the same-cohort mapping control now defaults to enabling applicable approved transitions, with an override; Year 10 Science and other subject cases remain pending. Grade conversions unchanged.

Deployment: replace app.py, transition_library.py, approved_subject_transitions.json and other Python source files from the release package. Confirm selected assessment columns and progress-coverage audit. Only synthetic data may be used on public free Streamlit hosting.

Tests: run `PYTHONPATH=. pytest -q` from the application directory. Live Streamlit browser not verified by automated tests.
