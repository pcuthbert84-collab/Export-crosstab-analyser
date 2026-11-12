import unittest
import pandas as pd
from engine import parse_grade,progress,classify_attainment,judgement,target_met,value_added,english_overlap,summarise

class Verification(unittest.TestCase):
 def g(self,x,k='auto'):return parse_grade(x,k)
 def test_ks3_me_gcse4_expected(self):self.assertEqual(progress(self.g('ME'),self.g('4')),'Expected')
 def test_ks3_me_plus_gcse6_expected(self):self.assertEqual(progress(self.g('ME+'),self.g('6')),'Expected')
 def test_ks3_me_plus_gcse5_less(self):self.assertEqual(progress(self.g('ME+'),self.g('5')),'Less')
 def test_gcse_high_override(self):self.assertEqual(progress(self.g('9'),self.g('7')),'Better')
 def test_curriculum_year(self):
  self.assertEqual(classify_attainment(self.g('Y3 EX'),4),'Below')
  self.assertEqual(classify_attainment(self.g('Y5 WT'),4),'Above')
 def test_targets(self):
  self.assertTrue(target_met(self.g('5'),self.g('5')))
  self.assertFalse(target_met(self.g('4'),self.g('5')))
 def test_double_grade_va(self):self.assertEqual(value_added(self.g('7,6'),self.g('6,5')),1.0)
 def test_double_grade_order(self):self.assertIsNone(self.g('6,4'))
 def test_judgement(self):
  self.assertEqual(judgement(74.5,74.5,20),'Outstanding')
  self.assertEqual(judgement(75,60.5,20),'Very Good')
  self.assertIsNone(judgement(100,100,4))
 def test_english_deduplication(self):
  df=pd.DataFrame([dict(student_id='A',year=5,category='English',subject='English',current_grade='ME'),dict(student_id='A',year=5,category='English',subject='Reading',current_grade='ME'),dict(student_id='B',year=5,category='English',subject='Reading',current_grade='ME')]);self.assertEqual(len(english_overlap(df)),2)
 def test_pooled_rate(self):
  rows=[]
  for i in range(100):rows.append(dict(student_id=str(i),subject='Maths',category='Mathematics',attainment='At' if i<80 else 'Below',progress='Expected'))
  for i in range(25):rows.append(dict(student_id=str(i),subject='Further Maths',category='Mathematics',attainment='At' if i<15 else 'Below',progress='Expected'))
  df=pd.DataFrame(rows);x=summarise(df,('category',));self.assertEqual(x['at_or_above'].iloc[0],76)
  y=summarise(df,('category',),'unweighted');self.assertEqual(y['at_or_above'].iloc[0],70)

if __name__=='__main__':unittest.main()
