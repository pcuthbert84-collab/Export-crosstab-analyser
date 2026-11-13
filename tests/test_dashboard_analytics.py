import unittest
import pandas as pd
from dashboard_analytics import filtered_cohort_summary, coverage_status, ppm_subject_counts, percentage_label, combined_assessments

class DashboardAnalyticsTests(unittest.TestCase):
    def test_uploaded_cohort_not_unweighted_subject_average(self):
        rows=[]
        for i in range(100):rows.append(dict(student_id=f'M{i}',year=8,subject='Maths',category='Mathematics',attainment='At' if i<80 else 'Below',progress='Expected',met_cat4=None,met_cat4_75=None,value_added=None))
        for i in range(25):rows.append(dict(student_id=f'F{i}',year=8,subject='Further Maths',category='Mathematics',attainment='At' if i<15 else 'Below',progress='Expected',met_cat4=None,met_cat4_75=None,value_added=None))
        frame=pd.DataFrame(rows)
        self.assertEqual(filtered_cohort_summary(frame)['at_or_above'],76)
        self.assertEqual(filtered_cohort_summary(frame,'unweighted')['at_or_above'],70)
    def test_phase_coverage_is_cautious(self):
        self.assertIn('Y8',coverage_status(pd.DataFrame({'year':[8,8]})))
    def test_ppm_counts_distinct_subjects(self):
        df=pd.DataFrame([
            {'student_id':'A','year':8,'subject':'English','concern_count':2},
            {'student_id':'A','year':8,'subject':'English','concern_count':1},
            {'student_id':'A','year':8,'subject':'Mathematics','concern_count':1},
            {'student_id':'B','year':8,'subject':'English','concern_count':0},
        ])
        result=ppm_subject_counts(df)
        self.assertEqual(result.iloc[0]['Subjects with concerns'],2)
        self.assertEqual(result.iloc[0]['Total concern flags'],4)
    def test_pct_half_up(self):self.assertEqual(percentage_label(74.5),'75%')
    def test_english_overlap(self):
        rows=[dict(student_id='A',year=5,subject='English',category='English',current_grade='ME'),dict(student_id='A',year=5,subject='Reading',category='English',current_grade='ME'),dict(student_id='B',year=5,subject='Writing',category='English',current_grade='ME')]
        self.assertEqual(len(combined_assessments(pd.DataFrame(rows))),2)

if __name__=='__main__':unittest.main()

class FocusTests(unittest.TestCase):
    def test_weak_focus_and_no_grade(self):
        from dashboard_analytics import focus_judgements
        f=pd.DataFrame([{'Subject':'A','KHDA grade':'Weak'},{'Subject':'B','KHDA grade':'Outstanding'},{'Subject':'C','KHDA grade':'—'}])
        self.assertEqual(focus_judgements(f,'Weak / Acceptable').Subject.tolist(),['A'])
        self.assertEqual(focus_judgements(f,'Without judgement').Subject.tolist(),['C'])

class CoverageTests(unittest.TestCase):
    def test_fallback_and_progress_counts_are_separate(self):
        from dashboard_analytics import assessment_coverage
        frame=pd.DataFrame([
            dict(current_grade='6',baseline_grade='5',current_source='DP1',baseline_source='Exam',progress='Better'),
            dict(current_grade='5',baseline_grade='4',current_source='Mock',baseline_source='DP3',progress=None),
            dict(current_grade=None,baseline_grade='5',current_source=None,baseline_source='DP3',progress=None),
        ])
        result=assessment_coverage(frame,'DP3','DP1')
        self.assertEqual(result['current_grade'],2)
        self.assertEqual(result['valid_progress'],1)
        self.assertEqual(result['current_from_fallback'],1)
        self.assertEqual(result['baseline_from_fallback'],1)

class PPMHotspotTests(unittest.TestCase):
    def test_count_unique_students_per_subject(self):
        from dashboard_analytics import ppm_subject_hotspots
        df=pd.DataFrame([
            dict(student_id='A',subject='English',concern_count=2),
            dict(student_id='A',subject='English',concern_count=1),
            dict(student_id='B',subject='English',concern_count=1),
            dict(student_id='B',subject='Maths',concern_count=1),
        ])
        h=ppm_subject_hotspots(df)
        self.assertEqual(h.loc[h.Subject.eq('English'),'Students with concerns'].iloc[0],2)
        self.assertEqual(h.loc[h.Subject.eq('English'),'Concern flags'].iloc[0],4)
