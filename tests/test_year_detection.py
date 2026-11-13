import pandas as pd
from year_detection import suggest_year

def test_detect_year_from_class_codes():
    data=pd.DataFrame({'Mathematics,  Class':['11A MAT','11B MAT','11D MAT'],'English,  Class':['11 ENG','11 ENG','11 ENG']})
    found=suggest_year('Export Crosstab (76).xlsx',[('data',data)])
    assert (found.year,found.source)==(11,'Class codes')

def test_detect_compact_class_codes():
    data=pd.DataFrame({'English,  Class':['8JPT ENG IAS3','8ABD ENG SAC3','8 MAT EDK'],'Year irrelevant':[2026]*3})
    assert suggest_year('Export.xlsx',[('sheet',data)]).year==8

def test_conflicting_years_require_selection():
    data=pd.DataFrame({'English,  Class':['8A ENG','8B ENG','8C ENG','11A ENG','11B ENG','11C ENG']})
    assert suggest_year('Export.xlsx',[('sheet',data)]).year is None

def test_filename_fallback():
    assert suggest_year('DCPro Year 5.xlsx',[('main',pd.DataFrame({'Student ID':['S1']}))]).year==5

def test_year_group_column():
    data=pd.DataFrame({'Year Group':[12,12,12]})
    assert suggest_year('export.xlsx',[('x',data)]).year==12

def test_unknown_does_not_fabricate_year_8():
    data=pd.DataFrame({'Mathematics, DP1 CPL / AG 2026/27':['Y5 ME','Y5 EX']})
    assert suggest_year('Export Crosstab (77).xlsx',[('data',data)]).year is None
