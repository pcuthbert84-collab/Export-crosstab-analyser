import io
import unittest
import pandas as pd
from openpyxl import load_workbook
from dashboard_exports import excel_bytes, pdf_summary

class ReportTests(unittest.TestCase):
    def test_excel_preserves_column_names_and_row_colours(self):
        df=pd.DataFrame([{'Subject':'Mathematics','Number':10,'KHDA grade':'Outstanding'}, {'Subject':'Science','Number':8,'KHDA grade':'Weak'}])
        excel=load_workbook(io.BytesIO(excel_bytes(df)))
        sh=excel['Results']
        self.assertEqual(sh['A1'].value,'Subject')
        self.assertEqual(sh['B2'].value,10)
        self.assertEqual(sh['A2'].fill.fgColor.rgb[-6:],'DBEAFE')
        self.assertEqual(sh['C3'].fill.fgColor.rgb[-6:],'FEE2E2')
        self.assertTrue(sh.freeze_panes)
    def test_pdf_stays_aggregate_summary(self):
        df=pd.DataFrame([dict(category='Maths',year=8,students=10,at_or_above=80.0,above=60.0,expected_plus=90.0,better=70.0,met_cat4=80.0,met_cat4_75=60.0,va=0.5,attainment_judgement='Good',progress_judgement='Very Good')])
        result=pdf_summary(df,'Synthetic only')
        self.assertTrue(result.startswith(b'%PDF'))
        self.assertGreater(len(result),1000)
if __name__=='__main__':unittest.main()
