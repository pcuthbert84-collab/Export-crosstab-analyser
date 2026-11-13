"""Static regression guard for the responsive assessment selector."""
from pathlib import Path


def test_assessment_switch_is_rerunning_radio_not_eager_tabs():
    app = (Path(__file__).resolve().parents[1] / 'app.py').read_text()
    block = app.split('def show_performance_tables(', 1)[1].split('def narrative_findings(', 1)[0]
    assert "'Assessment view', ['Attainment', 'Progress']" in block
    assert "key=f'{key}_assessment_view'" in block
    assert 'st.tabs(' not in block
    assert "table = att if kind == 'attainment' else prog" in block
    assert 'st.download_button(' in block


def test_presentation_key_has_inputs_that_must_invalidate():
    app = (Path(__file__).resolve().parents[1] / 'app.py').read_text()
    block = app.split('def show_performance_tables(', 1)[1].split('def narrative_findings(', 1)[0]
    for value in ('row.student_id', 'row.year', 'row.subject', 'row.attainment', 'row.progress',
                  'row.current_grade', 'row.target_grade', 'row.met_cat4', 'row.met_cat4_75'):
        assert value in block
