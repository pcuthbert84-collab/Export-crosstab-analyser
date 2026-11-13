import unittest
import pandas as pd
from engine import derive
from same_cohort_mapping import same_cohort_candidates, apply_same_cohort_mappings
from progress_coverage import progress_coverage

BASE='DP3 CPL / AG 2025/26'; EXAM='DP Exam Grade 2025/26'; CUR='DP1 CPL / AG 2026/27'

def fixture():
    rows=[]
    def r(student, year, subject, prior=None, exam=None, now=None):
        rows.append({'student_id':student,'year':year,'phase':3,'subject':subject,
                     'category':'English','source':'synthetic',BASE:prior,EXAM:exam,CUR:now})
    # Separate subject headings for this SAME student's previous/current year records.
    r('s1',11,'English',now='8')
    r('s1',11,'English Language',exam='7')
    r('s2',7,'English',now='4')
    r('s2',7,'Reading',prior='Y6 ME')
    r('s3',7,'English',now='7')
    r('s3',7,'Reading',prior='Y6 EX')
    r('s4',8,'English',prior='ME+',now='6')
    r('s4',8,'Reading',prior='ME')
    return pd.DataFrame(rows)

class TestSameCohortMapping(unittest.TestCase):
    def test_same_cohort_subject_candidates_detected(self):
        df=fixture();out=derive(df,BASE,EXAM,CUR,None,None,None)
        # Candidate discovery min 3 matches; create 3 synthetic variants.
        expanded=[]
        for prefix in ('A','B','C'):
            copy=df.copy();copy['student_id']=prefix+copy['student_id'];expanded.append(copy)
        many=pd.concat(expanded,ignore_index=True)
        suggestions=same_cohort_candidates(many,derive(many,BASE,EXAM,CUR,None,None,None),BASE,EXAM)
        self.assertTrue(any(s['year']==11 and s['subject']=='English' for s in suggestions))
        self.assertTrue(any(s['year']==7 and s['subject']=='English' for s in suggestions))

    def test_year11_exam_baseline_is_used_without_changing_attainment(self):
        df=fixture();before=derive(df,BASE,EXAM,CUR,None,None,None)
        after,audit=apply_same_cohort_mappings(before,df,{(11,'English'):['English Language']},BASE,EXAM)
        target=after[(after.year==11)&(after.subject=='English')].iloc[0]
        self.assertEqual(target.progress,'Better')
        self.assertEqual(target.current_grade,'8')
        self.assertEqual(target.attainment,before[(before.year==11)&(before.subject=='English')].iloc[0].attainment)
        self.assertEqual(audit.status.tolist(),['Mapped'])

    def test_year7_approved_me_to_gcse4(self):
        df=fixture();out=derive(df,BASE,EXAM,CUR,None,None,None)
        after,audit=apply_same_cohort_mappings(out,df,{(7,'English'):['Reading']},BASE,EXAM)
        self.assertEqual(after[(after.year==7)&(after.student_id=='s2')&(after.subject=='English')].iloc[0].progress,'Expected')
        self.assertIsNone(after[(after.year==7)&(after.student_id=='s3')&(after.subject=='English')].iloc[0].progress)
        self.assertIn('Needs approved conversion',audit.status.tolist())

    def test_existing_baseline_never_overridden(self):
        df=fixture();out=derive(df,BASE,EXAM,CUR,None,None,None)
        existing=out[(out.year==8)&(out.subject=='English')].iloc[0]
        after,_=apply_same_cohort_mappings(out,df,{(8,'English'):['Reading']},BASE,EXAM)
        same=after[(after.year==8)&(after.subject=='English')].iloc[0]
        self.assertEqual(same.baseline_grade,existing.baseline_grade)
        self.assertEqual(same.progress,existing.progress)

    def test_progress_coverage_aggregate_is_accurate(self):
        df=fixture();out=derive(df,BASE,EXAM,CUR,None,None,None)
        summary=progress_coverage(out[out.subject=='English'])
        y11=summary[summary.year==11].iloc[0]
        self.assertEqual(y11['Students with current grade'],1)
        self.assertEqual(y11['Progress classified'],0)
        self.assertEqual(y11['Current grade, baseline missing'],1)

if __name__=='__main__':unittest.main()


def test_approved_cross_category_computing_to_ict_is_discovered():
    from transition_library import load_library
    lib=load_library()
    rows=[]
    for i in range(4):
        sid=f'SYN{i}'
        rows.append(dict(student_id=sid,year=7,phase=3,subject='ICT',category='ICT',source='synthetic',**{BASE:None,CUR:'4'}))
        rows.append(dict(student_id=sid,year=7,phase=3,subject='Computing',category='Computing',source='synthetic',**{BASE:'Y6 ME',CUR:None}))
    src=pd.DataFrame(rows)
    result=derive(src,BASE,None,CUR,None,None,None)
    assert not any(c['subject']=='ICT' for c in same_cohort_candidates(src,result,BASE,None))
    matches=same_cohort_candidates(src,result,BASE,None,lib)
    assert any(c['subject']=='ICT' and c['sources'][0]['subject']=='Computing' for c in matches)
    new,audit=apply_same_cohort_mappings(result,src,{(7,'ICT'):['Computing']},BASE,None)
    assert new.loc[new.subject.eq('ICT'),'progress'].eq('Expected').all()
