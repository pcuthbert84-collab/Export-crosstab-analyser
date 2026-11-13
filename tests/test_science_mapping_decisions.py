"""Fictional students: exercise the approved Science subject mapping only."""
import pandas as pd
from engine import derive
from same_cohort_mapping import same_cohort_candidates, apply_same_cohort_mappings
from transition_library import load_library, is_explicitly_unmapped, find_rule
from progress_subject_mapping import _baseline_equivalent_point
from engine import parse_grade

BASE = 'DP3 CPL / AG 2025/26'
CURRENT = 'DP1 CPL / AG 2026/27'
SUBJECTS = ('Science - Combined','Science - Biology','Science - Chemistry','Science - Physics')


def fixture():
    rows=[]
    for i in range(6):
        sid=f'FAKE{i}'
        rows.append(dict(student_id=sid,year=10,phase=3,category='Science',subject='Science',source='synthetic',**{BASE:'ME+',CURRENT:None}))
        for s in SUBJECTS:
            now='7, 6' if s=='Science - Combined' else '7'
            rows.append(dict(student_id=sid,year=10,phase=3,category='Science',subject=s,source='synthetic',**{BASE:None,CURRENT:now}))
    return pd.DataFrame(rows)


def test_approved_science_baselines_detected_for_four_subjects():
    source=fixture()
    calculated=derive(source,BASE,None,CURRENT,None,None,None)
    candidates=same_cohort_candidates(source,calculated,BASE,None,load_library())
    for subject in SUBJECTS:
        item=next(c for c in candidates if c['year']==10 and c['subject']==subject)
        assert any(s['subject']=='Science' and s['students']==6 for s in item['sources'])
        assert find_rule(load_library(),10,subject,[s['subject'] for s in item['sources']],source_scope='same_cohort_prior_assessment')


def test_separate_sciences_and_combined_are_now_classified():
    source=fixture()
    calculated=derive(source,BASE,None,CURRENT,None,None,None)
    requested={(10,subject):['Science'] for subject in SUBJECTS}
    mapped,audit=apply_same_cohort_mappings(calculated,source,requested,BASE,None)
    assert len(mapped)==len(calculated)  # No extra result rows or duplicate pupils.
    for subject in SUBJECTS[1:]:
        filtered=mapped[mapped.subject.eq(subject)]
        assert len(filtered)==6 and filtered.progress.eq('Better').all()
        assert filtered.progress_baseline_sources.astype(str).str.contains('Science: ME+',regex=False).all()
    combined=mapped[mapped.subject.eq('Science - Combined')]
    assert len(combined)==6 and combined.progress.eq('Better').all()
    assert (audit.status=='Mapped').sum()==24
    assert (audit.status=='Needs approved conversion').sum()==0
    assert _baseline_equivalent_point(parse_grade('ME+'),parse_grade('7, 6'),9,subject='Science - Combined') == 6.0
    assert _baseline_equivalent_point(parse_grade('ME+'),parse_grade('7, 6'),9,subject='English') is None


def test_year7_drama_explicitly_unmapped():
    assert is_explicitly_unmapped(load_library(),7,'Drama')
