import pandas as pd
from engine import derive
from progress_subject_mapping import mapping_candidates, apply_subject_mappings


def setup_data():
    return pd.DataFrame([
        dict(student_id='S1',year=6,phase=2,subject='Reading',category='English',source='Y6',**{'DP3 CPL / AG 2025/26':'ME'}),
        dict(student_id='S1',year=6,phase=2,subject='Writing',category='English',source='Y6',**{'DP3 CPL / AG 2025/26':'ME+'}),
        dict(student_id='S1',year=7,phase=3,subject='English',category='English',source='Y7',**{'DP1 CPL / AG 2026/27':'ME+'}),
        dict(student_id='S2',year=6,phase=2,subject='Reading',category='English',source='Y6',**{'DP3 CPL / AG 2025/26':'ME'}),
        dict(student_id='S2',year=7,phase=3,subject='English',category='English',source='Y7',**{'DP1 CPL / AG 2026/27':'ME'}),
    ])


def derived(records):
    return derive(records,'DP3 CPL / AG 2025/26',None,'DP1 CPL / AG 2026/27',None,None,None)


def test_candidate_listing():
    c=mapping_candidates(setup_data(),'DP3 CPL / AG 2025/26')
    english=next(x for x in c if x['year']==7 and x['subject']=='English')
    assert set(['Reading','Writing']).issubset(english['sources'])
    assert english['matched_students']==2


def test_average_reading_writing():
    data=setup_data()
    old=derived(data)
    result,audit=apply_subject_mappings(old,data,{(7,'English'):['Reading','Writing']},'DP3 CPL / AG 2025/26')
    s1=result[(result.year==7)&(result.student_id=='S1')].iloc[0]
    assert s1.progress=='Better' # ME+ (6) > average(ME5,ME+6)=5.5
    assert s1.progress_baseline_mapping=='Average of mapped subjects'
    s2=result[(result.year==7)&(result.student_id=='S2')].iloc[0]
    assert s2.progress=='Expected' # only available Reading ME = current ME
    assert len(audit[audit.status=='Mapped'])==2


def test_single_subject():
    data=setup_data();r,a=apply_subject_mappings(derived(data),data,{(7,'English'):['Reading']},'DP3 CPL / AG 2025/26')
    s1=r[(r.year==7)&(r.student_id=='S1')].iloc[0]
    assert s1.progress=='Better'
    assert s1.progress_baseline_mapping=='Mapped single subject'


def test_no_mapping_means_no_change():
    data=setup_data();computed=derived(data)
    result,audit=apply_subject_mappings(computed,data,{},'DP3 CPL / AG 2025/26')
    assert result.progress.equals(computed.progress)
    assert audit.empty


def test_no_cross_student_leakage():
    data=setup_data()
    data.loc[(data.student_id=='S2')&(data.year==6),'student_id']='different-id'
    result,_=apply_subject_mappings(derived(data),data,{(7,'English'):['Reading']},'DP3 CPL / AG 2025/26')
    s2=result[(result.year==7)&(result.student_id=='S2')].iloc[0]
    assert pd.isna(s2.progress)


def test_existing_baseline_preserved():
    data=setup_data()
    mask=(data.year==7)&(data.student_id=='S1')
    data.loc[mask,'DP3 CPL / AG 2025/26']='ME+'
    result,_=apply_subject_mappings(derived(data),data,{(7,'English'):['Reading']},'DP3 CPL / AG 2025/26')
    s1=result[mask].iloc[0]
    assert s1.baseline_grade=='ME+'
    assert s1.progress=='Expected'
    assert s1.progress_baseline_mapping is None


def test_cross_grade_anchor():
    data=setup_data()
    data.loc[(data.student_id=='S1')&(data.year==7),'DP1 CPL / AG 2026/27']='4'
    r,a=apply_subject_mappings(derived(data),data,{(7,'English'):['Reading']},'DP3 CPL / AG 2025/26')
    s1=r[(r.student_id=='S1')&(r.year==7)].iloc[0]
    assert s1.progress=='Expected' # Year6 ME -> Year7 GCSE 4


def test_newly_approved_average_uses_both_sources():
    data=setup_data()
    data.loc[(data.student_id=='S1')&(data.year==6)&(data.subject=='Writing'),'DP3 CPL / AG 2025/26']='EX'
    data.loc[(data.student_id=='S1')&(data.year==7),'DP1 CPL / AG 2026/27']='4'
    r,a=apply_subject_mappings(derived(data),data,{(7,'English'):['Reading','Writing']},'DP3 CPL / AG 2025/26')
    s1=r[(r.student_id=='S1')&(r.year==7)].iloc[0]
    assert s1.progress=='Less'
    assert 'Mapped' in a.status.values
