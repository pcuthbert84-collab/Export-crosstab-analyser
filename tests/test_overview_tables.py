import unittest
import pandas as pd
from overview_tables import summary_tables, compact_table, whole_pct

class OverviewTables(unittest.TestCase):
    @staticmethod
    def fixture():
        return pd.DataFrame([
            dict(student_id='S1', year=8, subject='Maths', category='Mathematics', current_grade='6', target_grade='5', attainment='Above',progress='Better',met_cat4=True,met_cat4_75=True,value_added=1),
            dict(student_id='S2', year=8, subject='Maths', category='Mathematics', current_grade='4', target_grade='6', attainment='At',progress='Expected',met_cat4=False,met_cat4_75=False,value_added=-2),
            dict(student_id='S3', year=8, subject='Maths', category='Mathematics', current_grade=None,target_grade='5',attainment=None,progress=None,met_cat4=None,met_cat4_75=None,value_added=None),
        ])
    def test_rounding(self):
        self.assertEqual(whole_pct(74.5),'75%')
        self.assertEqual(whole_pct(None),'—')
    def test_valid_student_count_not_total_rows(self):
        a,p,g=summary_tables(self.fixture())
        self.assertEqual(a['Students with grades'].iloc[0],2)
        self.assertEqual(p['Students with both grades'].iloc[0],2)
        self.assertEqual(a['% Meeting or above'].iloc[0],'100%')
        self.assertEqual(a['Grade 4 · n'].iloc[0],1)
        self.assertEqual(a['Grade 6 · n'].iloc[0],1)
        self.assertEqual(a['Target-predicted at/above'].iloc[0],'100%')
        self.assertEqual(p['% Met CAT4 target'].iloc[0],'50%')
        self.assertEqual(p['CAT4 eligible (n)'].iloc[0],2)
    def test_compact_keeps_only_requested_columns(self):
        a,p,g=summary_tables(self.fixture())
        self.assertEqual(list(compact_table(a,('category',),'attainment').columns), ['category','Students with grades','Grade results (n)','% Meeting or above','% Exceeding','KHDA grade'])
        self.assertFalse('Less · n' in compact_table(p,('category',),'progress').columns)

if __name__=='__main__':unittest.main()
