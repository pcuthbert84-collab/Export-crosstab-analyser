"""Approved BTEC IT conversion checks; no real student data retained in release."""
import pandas as pd
import pytest
from engine import parse_grade, progress, derive
from btec_it_grade_conversions import ICT_TO_BTEC, BTEC_RANK
from same_cohort_mapping import apply_same_cohort_mappings
from transition_library import load_library, find_rule

BASE='DP3 CPL / AG 2025/26'
CUR='DP1 CPL / AG 2026/27'

@pytest.mark.parametrize('descriptor,expected', list(ICT_TO_BTEC.items()))
def test_every_approved_descriptor_has_expected_btec_result(descriptor, expected):
    baseline = parse_grade(descriptor)
    exact = parse_grade(expected,'btec')
    assert progress(baseline,exact,10,9,'BTEC IT')=='Expected'
    higher = next((level for level, rank in BTEC_RANK.items() if rank == BTEC_RANK[expected]+1),None)
    lower = next((level for level, rank in BTEC_RANK.items() if rank == BTEC_RANK[expected]-1),None)
    if higher:
        assert progress(baseline,parse_grade(higher,'btec'),10,9,'BTEC IT')=='Better'
    if lower:
        assert progress(baseline,parse_grade(lower,'btec'),10,9,'BTEC IT')=='Less'

@pytest.mark.parametrize('descriptor',['WT-','WT','WT+','ME-','ME','ME+','EX-','EX','MA'])
def test_btec_conversion_is_scoped(descriptor):
    assert progress(parse_grade(descriptor),parse_grade('Merit','btec'),10,9,'Business') is None
    assert progress(parse_grade(descriptor),parse_grade('Merit','btec'),10,9,'Computer Science') is None

def test_approved_subject_mapping_retained():
    rule=find_rule(load_library(),10,'BTEC IT',['ICT'],source_scope='same_cohort_prior_assessment')
    assert rule is not None

def test_same_cohort_mapping_uses_approved_btec_conversion():
    entries=[]
    for i,(base,current,expected) in enumerate([
        ('ME-','Pass','Better'),('ME','Pass','Expected'),('ME','Merit','Better'),
        ('ME+','Merit','Expected'),('ME+','Distinction','Better'),
        ('EX-','Merit','Less'),('EX','Distinction','Expected'),('MA','Distinction','Less'),
        ('MA','Distinction*','Expected'),('WT','Fail','Expected'),('ME+','U','Less'),
    ]):
        sid=f'SYNTHETIC_{i}'
        entries.extend([
            dict(student_id=sid,year=10,subject='BTEC IT',category='BTEC IT',phase=3,source='test',**{BASE:None,CUR:current}),
            dict(student_id=sid,year=10,subject='ICT',category='ICT',phase=3,source='test',**{BASE:base,CUR:None}),
        ])
    records=pd.DataFrame(entries)
    calculated=derive(records,BASE,None,CUR,None,None,None)
    mapped,audit=apply_same_cohort_mappings(calculated,records,{(10,'BTEC IT'):['ICT']},BASE,None)
    assert list(mapped[mapped.subject.eq('BTEC IT')].progress)==[
        'Better','Expected','Better','Expected','Better','Less','Expected','Less','Expected','Expected','Less'
    ]
    assert (audit.status=='Mapped').sum()==11
    assert len(mapped)==len(calculated)
    assert mapped[mapped.subject.eq('BTEC IT')].attainment.notna().all()

def test_normal_btec_to_btec_progress_unchanged():
    assert progress(parse_grade('Pass','btec'),parse_grade('Merit','btec'),10,9,'BTEC IT')=='Better'
    assert progress(parse_grade('Merit','btec'),parse_grade('Merit','btec'),10,9,'BTEC IT')=='Expected'
    assert progress(parse_grade('Distinction','btec'),parse_grade('Pass','btec'),10,9,'BTEC IT')=='Less'
