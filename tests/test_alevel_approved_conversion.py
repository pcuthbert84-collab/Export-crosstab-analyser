"""Policy tests: approved GCSE -> A Level expected progress across ALL A Levels."""
import pytest
import pandas as pd
from engine import parse_grade, progress, derive
from alevel_grade_conversions import GCSE_TO_ALEVEL, gcse_to_alevel_expected
from progress_subject_mapping import _baseline_equivalent_point, _mapped_progress
from same_cohort_mapping import apply_same_cohort_mappings

@pytest.mark.parametrize('gcse,expected',sorted(GCSE_TO_ALEVEL.items()))
def test_approved_destination(gcse,expected):
    base=parse_grade(str(gcse),'gcse'); destination=parse_grade(expected,'alevel')
    assert gcse_to_alevel_expected(base,destination)==destination.point

@pytest.mark.parametrize('subject',['Mathematics','English Literature','Physics','Psychology','History'])
def test_all_alevel_subjects_use_same_rule(subject):
    base=parse_grade('6','gcse'); actual=parse_grade('B','alevel')
    assert progress(base,actual,current_year=12,subject=subject)=='Expected'
    assert progress(base,parse_grade('C','alevel'),current_year=12,subject=subject)=='Less'
    assert progress(base,parse_grade('A','alevel'),current_year=12,subject=subject)=='Better'

@pytest.mark.parametrize('gcse',['7','8','9'])
@pytest.mark.parametrize('alevel',['A','A*'])
def test_high_achievement_override(gcse,alevel):
    assert progress(parse_grade(gcse,'gcse'),parse_grade(alevel,'alevel'),current_year=12)=='Better'


def test_same_workbook_grade_selection_and_current_grade():
    prior='DP3 CPL / AG 2025/26'; current='DP1 CPL / AG 2026/27'
    records=pd.DataFrame([{'student_id':'SYN-1','year':12,'phase':4,'subject':'Mathematics','category':'Mathematics','source':'synthetic',prior:'4',current:'C'},
                          {'student_id':'SYN-2','year':12,'phase':4,'subject':'Physics','category':'Science','source':'synthetic',prior:'9',current:'A*'},
                          {'student_id':'SYN-3','year':12,'phase':4,'subject':'History','category':'History','source':'synthetic',prior:'2',current:'E'}])
    result=derive(records,prior,None,current,None,None,None)
    assert result.progress.tolist()==['Expected','Better','Expected']
    assert result.baseline_grade.tolist()==['4','9','2']
    assert result.current_grade.tolist()==['C','A*','E']


def test_within_alevel_progress_unchanged():
    assert progress(parse_grade('D','alevel'),parse_grade('C','alevel'),12)=='Better'
    assert progress(parse_grade('B','alevel'),parse_grade('B','alevel'),13)=='Expected'
    assert progress(parse_grade('B','alevel'),parse_grade('C','alevel'),13)=='Less'


def test_unapproved_gcse_u_is_not_a_gcse_to_alevel_expected_destination():
    assert gcse_to_alevel_expected(parse_grade('U','gcse'),parse_grade('U','alevel')) is None
    assert progress(parse_grade('U','gcse'),parse_grade('U','alevel')) is None


def test_mapped_same_cohort_grade_uses_approved_conversion():
    prior='DP3 CPL / AG 2025/26';current='DP1 CPL / AG 2026/27'
    rows=[dict(student_id='SYN-1',year=12,phase=4,subject='Further Mathematics',category='Mathematics',source='synthetic',**{prior:None,current:'C'}),
          dict(student_id='SYN-1',year=12,phase=4,subject='Mathematics',category='Mathematics',source='synthetic',**{prior:'4',current:None})]
    records=pd.DataFrame(rows)
    calc=derive(records,prior,None,current,None,None,None)
    updated,audit=apply_same_cohort_mappings(calc,records,{(12,'Further Mathematics'):['Mathematics']},prior)
    assert updated.loc[updated.subject.eq('Further Mathematics'),'progress'].iloc[0]=='Expected'
    assert not audit.empty


def test_unrelated_btec_not_mapped():
    assert gcse_to_alevel_expected(parse_grade('6','gcse'),parse_grade('Merit','btec')) is None
