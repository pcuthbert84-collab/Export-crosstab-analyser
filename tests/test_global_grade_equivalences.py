"""Grade conversion and same-workbook fallback regressions."""
import pandas as pd
import pytest
from grade_equivalences import DESCRIPTOR_TO_GCSE, baseline_equivalent
from engine import parse_grade, parse_dcpro, select_grade, derive, progress, classify_attainment, target_met
from progress_subject_mapping import _baseline_equivalent_point
from same_cohort_mapping import apply_same_cohort_mappings

BASE='DP3'
BACK='Exam'
CURRENT='DP1'
CURRENT_BACK='Mock'

@pytest.mark.parametrize('subject', ['English','Mathematics','History','Geography','Technology','ICT','Drama','Science - Combined','Psychology'])
@pytest.mark.parametrize('descriptor,grade', list(DESCRIPTOR_TO_GCSE.items()))
def test_every_subject_approved_descriptor_mapping(subject,descriptor,grade):
    old=parse_grade(descriptor)
    new=parse_grade(str(grade))
    double=parse_grade(f'{grade},{grade}')
    assert baseline_equivalent(old,new)==grade
    assert _baseline_equivalent_point(old,new,9,subject)==grade
    assert _baseline_equivalent_point(old,double,9,subject)==grade
    assert progress(old,new,10,9,subject)==('Better' if grade>=7 else 'Expected')
    assert progress(old,double,10,9,subject)==('Better' if grade>=7 else 'Expected')

def test_u_is_zero_for_all_supported_grade_kinds():
    for kind in ('auto','gcse','alevel','btec'):
        u=parse_grade(' U ',kind)
        assert u is not None and u.point==0
    assert classify_attainment(parse_grade('U','gcse'),10)=='Below'
    assert classify_attainment(parse_grade('U','alevel'),12)=='Below'
    assert progress(parse_grade('ME'),parse_grade('U'),10,9,'English')=='Less'
    assert target_met(parse_grade('U'),parse_grade('1')) is False

def test_na_or_invalid_first_assessment_uses_fallback_in_same_workbook():
    record={'student_id':'synthetic','year':10,'phase':3,'subject':'History','category':'History','source':'synthetic',BASE:'N/A',BACK:'ME+',CURRENT:' n/a ',CURRENT_BACK:'6'}
    derived=derive(pd.DataFrame([record]), BASE, BACK, CURRENT, CURRENT_BACK, None, None)
    row=derived.iloc[0]
    assert row.baseline_grade=='ME+'
    assert row.current_grade=='6'
    assert row.baseline_source==BACK
    assert row.current_source==CURRENT_BACK
    assert row.progress=='Expected'
    assert select_grade(record,BASE,BACK)[0].level=='ME+'
    record[BASE]='Na'
    assert select_grade(record,BASE,BACK)[0].level=='ME+'

def test_u_is_valid_and_does_not_trigger_fallback():
    grade,src=select_grade({'DP1':'U','Mock':'6'},'DP1','Mock')
    assert grade.point==0 and src=='DP1'

def test_no_leak_to_unapproved_subject_transitions():
    # Conversion applies globally; it does not invent a subject baseline.
    records=pd.DataFrame([dict(student_id='synthetic',year=7,phase=3,subject='Drama',category='Drama',source='synthetic',DP3=None,DP1='4'),
                          dict(student_id='synthetic',year=7,phase=3,subject='Technology',category='Technology',source='synthetic',DP3='ME',DP1=None)])
    calculated=derive(records,'DP3',None,'DP1',None,None,None)
    mapped,audit=apply_same_cohort_mappings(calculated,records,{},'DP3')
    assert pd.isna(mapped.loc[mapped.subject.eq('Drama'),'progress'].iloc[0])
    assert audit.empty


def test_actual_xlsx_ingest_uses_same_file_baseline_current_and_fallback():
    import io
    synthetic=pd.DataFrame({
        'Student ID':['synthetic-1','synthetic-2','synthetic-3'],
        'Mathematics, DP3':['ME','N/A','ME+'],
        'Mathematics, Exam':['4','EX-','ME-'],
        'Mathematics, DP1':['4','U',' N/A '],
        'Mathematics, Mock':['5','6','6'],
    })
    b=io.BytesIO()
    with pd.ExcelWriter(b,engine='openpyxl') as w:
        synthetic.to_excel(w,index=False)
    b.seek(0)
    frame=pd.read_excel(b, dtype=object)
    records=parse_dcpro(frame,year=10,source_name='synthetic.xlsx')
    result=derive(records,'DP3','Exam','DP1','Mock',None,None)
    rows=result.set_index('student_id')
    assert rows.loc['synthetic-1','progress']=='Expected'   # ME -> 4; preferred has precedence
    assert rows.loc['synthetic-2','progress']=='Less'       # EX- -> U=0; U is valid, not missing
    assert rows.loc['synthetic-3','progress']=='Expected'   # ME+ -> fallback Mock=6
    assert rows.loc['synthetic-2','baseline_source']=='Exam'
    assert rows.loc['synthetic-2','current_source']=='DP1'
    assert rows.loc['synthetic-3','current_source']=='Mock'


def test_btec_u_is_below_standard_and_zero():
    g=parse_grade('U',kind='btec')
    assert g.kind=='btec' and g.point==0
    assert classify_attainment(g,10)=='Below'
    assert progress(parse_grade('PASS',kind='btec'),g,10,9,'BTEC IT')=='Less'
