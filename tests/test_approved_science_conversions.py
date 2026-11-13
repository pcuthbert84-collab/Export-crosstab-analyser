"""Regression tests for Science-only school-approved descriptor conversions."""
import pandas as pd
import pytest
from engine import parse_grade, progress, derive
from science_grade_conversions import SCIENCE_DESCRIPTOR_TO_GCSE, science_equivalence, paired_science_equivalent
from same_cohort_mapping import apply_same_cohort_mappings
from progress_subject_mapping import apply_subject_mappings

BASE='DP3 CPL / AG 2025/26'
CUR='DP1 CPL / AG 2026/27'

@pytest.mark.parametrize('descriptor,n',list(SCIENCE_DESCRIPTOR_TO_GCSE.items()))
def test_every_approved_science_single_and_double_equivalent(descriptor,n):
    prev=parse_grade(descriptor)
    cur=parse_grade(str(n))
    pair=parse_grade(f'{n}, {n}')
    assert science_equivalence(prev,cur,'Science - Biology')==n
    assert science_equivalence(prev,pair,'Science - Combined')==n
    assert paired_science_equivalent(descriptor)==f'{n},{n}'
    # High-grade achievement rule from engine remains in effect.
    result='Better' if n>=7 else 'Expected'
    assert progress(prev,cur,10,9,subject='Science - Biology')==result
    assert progress(prev,pair,10,9,subject='Science - Combined')==result

@pytest.mark.parametrize('baseline,actual,expected',[('ME','4, 4','Expected'),('ME','4, 3','Less'),
    ('ME','5, 4','Better'),('ME+','6, 6','Expected'),('ME+','6, 5','Less'),
    ('ME+','7, 6','Better'),('WT+','3','Expected'),('ME-','3','Expected'),
    ('EX','9','Better'),('Y9 ME','4, 4','Expected')])
def test_science_progress_examples(baseline,actual,expected):
    assert progress(parse_grade(baseline),parse_grade(actual),10,9,subject='Science - Combined')==expected

def test_all_subjects_share_approved_conversions():
    for label,n in SCIENCE_DESCRIPTOR_TO_GCSE.items():
        assert progress(parse_grade(label), parse_grade(str(n)), 10, 9, subject='Mathematics') == ('Better' if n>=7 else 'Expected')
        assert progress(parse_grade(label), parse_grade(f'{n},{n}'), 10, 9, subject='English') == ('Better' if n>=7 else 'Expected')
    assert science_equivalence(parse_grade('ME'),parse_grade('4'),'BTEC Science') is None


def test_direct_science_rows_convert_without_changing_attainment():
    record=pd.DataFrame([{'student_id':'f1','year':10,'phase':3,'subject':'Science', 'category':'Science',
                          'source':'synthetic',BASE:'ME-',CUR:'3'},
                         {'student_id':'f2','year':10,'phase':3,'subject':'English', 'category':'English',
                          'source':'synthetic',BASE:'ME-',CUR:'3'}])
    computed=derive(record,BASE,None,CUR,None,None,None)
    assert computed.loc[computed.subject.eq('Science'),'progress'].iloc[0]=='Expected'
    assert computed.loc[computed.subject.eq('English'),'progress'].iloc[0]=='Expected'


def test_same_cohort_mapping_science_pairs_and_non_science_unchanged():
    rows=[]
    for sid,prior,combined,biology in [('p1','ME','4, 4','4'),('p2','ME+','6, 5','6'),('p3','WT+','3, 3','3')]:
        for sub,old,now in [('Science',prior,None),('Science - Combined',None,combined),('Science - Biology',None,biology)]:
            rows.append({'student_id':sid,'year':10,'phase':3,'subject':sub,'category':'Science','source':'synthetic',BASE:old,CUR:now})
    records=pd.DataFrame(rows)
    before=derive(records,BASE,None,CUR,None,None,None)
    chosen={(10,'Science - Combined'):['Science'],(10,'Science - Biology'):['Science']}
    after,audit=apply_same_cohort_mappings(before,records,chosen,BASE,None)
    assert len(after)==len(before)
    assert (audit.status=='Mapped').sum()==6
    p1=after[(after.student_id=='p1') & (after.subject=='Science - Combined')].iloc[0]
    p2=after[(after.student_id=='p2') & (after.subject=='Science - Combined')].iloc[0]
    assert p1.progress=='Expected' and p2.progress=='Less'
    assert p2.attainment==before[(before.student_id=='p2') & (before.subject=='Science - Combined')].iloc[0].attainment
    assert after[after.subject.eq('Science')]['progress'].isna().all()


def test_cross_year_mapping_uses_same_science_rule():
    records=pd.DataFrame([
      {'student_id':'f1','year':9,'phase':3,'subject':'Science','category':'Science','source':'synthetic',BASE:'ME',CUR:None},
      {'student_id':'f1','year':10,'phase':3,'subject':'Science - Combined','category':'Science','source':'synthetic',BASE:None,CUR:'4, 4'},
    ])
    before=derive(records,BASE,None,CUR,None,None,None)
    after,audit=apply_subject_mappings(before,records,{(10,'Science - Combined'):['Science']},BASE,None)
    assert after.loc[after.subject.eq('Science - Combined'),'progress'].iloc[0]=='Expected'
    assert audit.status.tolist()==['Mapped']
