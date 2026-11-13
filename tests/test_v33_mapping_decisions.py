import pandas as pd
from engine import derive
from progress_policy import apply_reporting_policy
from transition_library import load_library,find_rule,is_explicitly_unmapped
from same_cohort_mapping import same_cohort_candidates,apply_same_cohort_mappings

BASE='DP3 CPL / AG 2025/26'
CUR='DP1 CPL / AG 2026/27'

def test_v33_approved_subject_rules_are_present_and_scoped():
    lib=load_library()
    for current,src in [('Design Technology','Technology'),('BTEC IT','ICT'),('Computer Science','ICT')]:
        rule=find_rule(lib,10,current,[src],source_scope='same_cohort_prior_assessment')
        assert rule and rule['resolved_sources']==[src]
    triple=find_rule(lib,11,'Triple Science',['Science - Biology','Science - Chemistry','Science - Physics'],source_scope='same_cohort_prior_assessment')
    assert triple and triple['method']=='mean_available'
    assert is_explicitly_unmapped(lib,10,'Business')
    assert is_explicitly_unmapped(lib,10,'Psychology')
    assert not any(r['to_year']==12 and r['current_subject']=='Mathematics' for r in lib['rules'])

def test_cross_category_year10_mappings_and_btec_conversion_approved():
    rows=[]
    for i in range(4):
        sid=f'FAKE-{i}'
        for sub,curr,prior in [('Design Technology','6',None),('Technology',None,'ME+'),('Computer Science','6',None),('BTEC IT','Merit',None),('ICT',None,'ME+')]:
            rows.append(dict(student_id=sid,year=10,subject=sub,category=sub,phase=3,source='synthetic',**{CUR:curr,BASE:prior}))
    records=pd.DataFrame(rows)
    derived=derive(records,BASE,None,CUR,None,None,None)
    lib=load_library()
    candidates=same_cohort_candidates(records,derived,BASE,None,lib)
    assert any(c['subject']=='Design Technology' for c in candidates)
    assert any(c['subject']=='BTEC IT' for c in candidates)
    assert any(c['subject']=='Computer Science' for c in candidates)
    mappings={(10,'Design Technology'):['Technology'],(10,'BTEC IT'):['ICT'],(10,'Computer Science'):['ICT']}
    mapped,audit=apply_same_cohort_mappings(derived,records,mappings,BASE,None)
    assert mapped[mapped.subject.eq('Design Technology')].progress.eq('Expected').all()
    assert mapped[mapped.subject.eq('Computer Science')].progress.eq('Expected').all()
    assert mapped[mapped.subject.eq('BTEC IT')].progress.eq('Expected').all()
    assert (audit.status=='Needs approved conversion').sum()==0

def test_triple_science_sources_are_averaged_once_per_current_subject():
    rows=[]
    for i in range(4):
        for sub,curr,prior in [('Triple Science','6',None),('Science - Biology',None,'5'),('Science - Chemistry',None,'6'),('Science - Physics',None,'7')]:
            rows.append(dict(student_id=f'FAKE-{i}',year=11,subject=sub,category='Science',phase=3,source='synthetic',**{CUR:curr,BASE:prior}))
    records=pd.DataFrame(rows);out=derive(records,BASE,None,CUR,None,None,None)
    cand=same_cohort_candidates(records,out,BASE,None,load_library())
    assert any(c['subject']=='Triple Science' for c in cand)
    mapped,audit=apply_same_cohort_mappings(out,records,{(11,'Triple Science'):['Science - Biology','Science - Chemistry','Science - Physics']},BASE,None)
    triple=mapped[mapped.subject.eq('Triple Science')]
    assert len(triple)==4 and triple.progress.eq('Expected').all()
    assert (audit.status=='Mapped').sum()==4
    assert len(mapped)==len(records)

def test_new_gcse_courses_require_two_valid_assessments():
    lib=load_library()
    data=pd.DataFrame([dict(student_id='s1',year=10,subject='Business',category='Business',phase=3,source='synthetic',**{BASE:None,CUR:'5'}),dict(student_id='s2',year=10,subject='Psychology',category='Psychology',phase=3,source='synthetic',**{BASE:'4',CUR:'5'})])
    out=apply_reporting_policy(derive(data,BASE,None,CUR,None,None,None),lib)
    assert out.iloc[0]['Progress basis']=='Within-course: awaiting comparable assessments'
    assert pd.isna(out.iloc[0].progress)
    assert out.iloc[1]['Progress basis']=='Within-course progress'
    assert out.iloc[1].progress=='Better'

def test_existing_eng_science_and_no_mapping_rules_survive():
    lib=load_library()
    assert find_rule(lib,7,'English',['Reading','Writing'],source_scope='same_cohort_prior_assessment')
    assert find_rule(lib,10,'Science - Combined',['Science'],source_scope='same_cohort_prior_assessment')
    assert is_explicitly_unmapped(lib,7,'Drama')
    assert is_explicitly_unmapped(lib,7,'Geography')
