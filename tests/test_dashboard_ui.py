import unittest
import pandas as pd
from dashboard_ui import metric_bars, row_style, grade_legend_html, judgement_mix

class DashboardUiTests(unittest.TestCase):
    def test_summary_chart_shows_both_measures(self):
        df=pd.DataFrame([{'category':'Mathematics','at_or_above':85,'above':61,'at_or_above_n':40,'above_n':40}])
        fig=metric_bars(df)
        self.assertEqual(len(fig.data),2)
        self.assertEqual(fig.data[0].orientation,'h')
    def test_judgement_row_colouring(self):
        df=pd.DataFrame([{'Subject':'Maths','KHDA grade':'Outstanding'},{'Subject':'Science','KHDA grade':'Weak'}])
        ctx=row_style(df)._compute().ctx
        self.assertIn(('background-color', '#dbeafe'),ctx[(0,0)])
        self.assertIn(('background-color', '#fee2e2'),ctx[(1,1)])
    def test_legend(self):self.assertIn('Very Good',grade_legend_html())
if __name__=='__main__':unittest.main()

class DistributionChartTests(unittest.TestCase):
    def test_distribution_chart_has_total_count(self):
        from dashboard_ui import grade_distribution_chart
        f=pd.DataFrame([{'Grade':'6','Count':3,'Percent':60},{'Grade':'5','Count':2,'Percent':40}])
        fig=grade_distribution_chart(f)
        self.assertEqual(sum(fig.data[0].y),5)
        self.assertEqual(list(fig.data[0].x),['6','5'])

class SortingTests(unittest.TestCase):
    def test_chart_prioritises_lowest_or_highest(self):
        rows=[]
        for i,n in enumerate(['Maths','English','Science']):
            rows.append(dict(category=n,at_or_above=[70,95,80][i],above=50,at_or_above_n=30,above_n=30))
        df=pd.DataFrame(rows)
        low=metric_bars(df,priority='lowest',limit=2)
        high=metric_bars(df,priority='highest',limit=2)
        self.assertEqual(set(low.data[0].y),{'Maths','Science'})
        self.assertEqual(set(high.data[0].y),{'English','Science'})
