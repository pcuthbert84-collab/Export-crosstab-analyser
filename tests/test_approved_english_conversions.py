"""Regression checks for English scope, single and same-cohort mapping and audit."""
import pandas as pd
import pytest
from engine import parse_grade, progress, derive
from english_grade_conversions import english_equivalence, ENGLISH_DESCRIPTOR_TO_GCSE
from same_cohort_mapping import apply_same_cohort_mappings
from progress_subject_mapping import apply_subject_mappings
from progress_coverage import progress_coverage

B='DP3 CPL / AG 2025/26'; C='DP1 CPL / AG 2026/27'

@pytest.mark.parametrize('descriptor,expected',ENGLISH_DESCRIPTOR_TO_GCSE.items())
def test_english_all_equivalences(descriptor,expected):
    b=parse_grade('Y6 '+descriptor); c=parse_grade(str(expected))
    assert english_equivalence(b,c,'English')==expected
    assert english_equivalence(b,c,'Mathematics') is None
    assert english_equivalence(b,parse_grade(f'{expected},{expected}'),'English') is None
    assert progress(b,c,7,6,subject='English') == ('Better' if expected>=7 else 'Expected')

@pytest.mark.parametrize('name',('Mathematics','Geography','ICT','Technology','Drama'))
def test_non_english_no_new_conversions(name):
    assert progress(parse_grade('WT-'),parse_grade('1'),10,9,subject=name) is None


def test_year7_mean_and_year11_language_preserved():
    data=pd.DataFrame([
        dict(student_id='a',year=7,phase=3,subject='English',category='English',source='synthetic',**{B:None,C:'6'}),
        dict(student_id='a',year=7,phase=3,subject='Reading',category='English',source='synthetic',**{B:'Y6 ME',C:None}),
        dict(student_id='a',year=7,phase=3,subject='Writing',category='English',source='synthetic',**{B:'Y6 EX-',C:None}),
        dict(student_id='b',year=11,phase=3,subject='English',category='English',source='synthetic',**{B:None,C:'6'}),
        dict(student_id='b',year=11,phase=3,subject='English Language',category='English',source='synthetic',**{B:'5',C:None}),
    ])
    result,audit=apply_same_cohort_mappings(derive(data,B,None,C,None,None,None),data,
        {(7,'English'):['Reading','Writing'],(11,'English'):['English Language']},B)
    assert result[(result.student_id=='a')&(result.subject=='English')].iloc[0].progress=='Better' # (4+7)/2 = 5.5; current 6
    assert result[(result.student_id=='b')&(result.subject=='English')].iloc[0].progress=='Better'
    assert audit.status.eq('Mapped').sum()==2


def test_missing_and_unsupported_source_reported_separately():
    data=pd.DataFrame([
        dict(student_id='a',year=7,phase=3,subject='English',category='English',source='synthetic',**{B:None,C:'4'}),
        dict(student_id='a',year=7,phase=3,subject='Reading',category='English',source='synthetic',**{B:'Y6 ME',C:None}),
        dict(student_id='a',year=7,phase=3,subject='Writing',category='English',source='synthetic',**{B:'Y6 ME',C:None}),
        dict(student_id='b',year=7,phase=3,subject='English',category='English',source='synthetic',**{B:None,C:'4'}),
        dict(student_id='b',year=7,phase=3,subject='Reading',category='English',source='synthetic',**{B:'A',C:None}),
        dict(student_id='c',year=7,phase=3,subject='English',category='English',source='synthetic',**{B:None,C:'4'}),
    ])
    result,audit=apply_same_cohort_mappings(derive(data,B,None,C,None,None,None),data,{(7,'English'):['Reading','Writing']},B)
    cov=progress_coverage(result[result.subject.eq('English')]).iloc[0]
    assert cov['Progress classified']==1
    assert cov['Current grade, baseline missing']==1
    assert cov['Grade conversion not approved']==1
    assert cov['Source found but conversion blocked']==1
