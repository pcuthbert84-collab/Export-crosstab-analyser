"""Presentation analytics for the DBSJP prototype.

Pure functions: no Streamlit imports, I/O, shared caches, or persistent records.
All student-level data must remain local to the caller's in-memory session.
"""
from __future__ import annotations
import pandas as pd
from engine import summarise, english_overlap, judgement

PHASES = {
    1: ('Phase 1', 'FS1–FS2 · EYFS planned for v2'),
    2: ('Phase 2', 'Years 1–6'),
    3: ('Phase 3', 'Years 7–11'),
    4: ('Phase 4', 'Years 12–13'),
}

GRADE_COLORS = {
    'Outstanding': '#dbeafe',
    'Very Good': '#dcfce7',
    'Good': '#fef9c3',
    'Acceptable': '#ffedd5',
    'Weak': '#fee2e2',
}
GRADE_TEXT = {
    'Outstanding': '#1d4ed8',
    'Very Good': '#166534',
    'Good': '#854d0e',
    'Acceptable': '#9a3412',
    'Weak': '#991b1b',
}


def combined_assessments(data):
    """Apply English overlap only to combined subject-level aggregates."""
    if data.empty:
        return data.copy()
    other = data.loc[data['category'].ne('English')]
    return pd.concat([other, english_overlap(data)], ignore_index=True)


def filtered_cohort_summary(data, method='pooled'):
    """Aggregate the selected uploaded population, NOT the complete school."""
    if data.empty:
        return {}
    work=data.assign(_cohort='Uploaded cohort')
    summary=summarise(work, ('_cohort',), method=method)
    if summary.empty:
        return {}
    return summary.iloc[0].to_dict()


def year_coverage(data):
    return sorted(int(y) for y in data['year'].dropna().unique()) if not data.empty else []


def percentage_label(value, missing='—'):
    from decimal import Decimal, ROUND_HALF_UP
    if value is None or pd.isna(value):
        return missing
    return f"{int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%"


def coverage_status(data):
    """Warn users when the subset does not cover a whole school or phase."""
    years=set(year_coverage(data))
    if not years:
        return 'No uploaded year groups in the selected scope.'
    return 'Uploaded year groups: '+', '.join(f'Y{y}' for y in sorted(years))+'. Figures represent this selection only.'


def tidy_summary(summary, *, include_year=False):
    """Turn raw engine keys into a small useful analysis table."""
    mapping={
        'category':'Subject','subject':'Subject','year':'Year','students':'Students',
        'at_or_above':'Meeting+','above':'Exceeding',
        'expected_plus':'Expected+','better':'Better+',
        'attainment_judgement':'Attainment grade',
        'progress_judgement':'Progress grade',
        'met_cat4':'Met CAT4','met_cat4_75':'Met challenge','va':'Mean VA',
    }
    if summary.empty:return summary.copy()
    result=summary.rename(columns=mapping)
    return result


def ppm_subject_counts(data):
    """One row per student/year, counting UNIQUE affected subjects."""
    if data.empty:
        return pd.DataFrame(columns=['student_id','year','Subjects with concerns','Total concern flags','Priority'])
    working=data.loc[data['concern_count'].fillna(0)>0].copy()
    if working.empty:
        return pd.DataFrame(columns=['student_id','year','Subjects with concerns','Total concern flags','Priority'])
    grouped=working.groupby(['student_id','year'],dropna=False).agg(
        **{'Subjects with concerns':('subject','nunique'),
           'Total concern flags':('concern_count','sum')}
    ).reset_index()
    grouped['Priority']=grouped['Subjects with concerns'].map(
        lambda n:'3+ subjects' if n>=3 else '2 subjects' if n==2 else '1 subject')
    return grouped.sort_values(['Subjects with concerns','Total concern flags','student_id'],ascending=[False,False,True]).reset_index(drop=True)


def subject_coverage(data):
    """Number of uniquely represented students and valid assessment records per subject."""
    if data.empty:return pd.DataFrame(columns=['Subject','Students','Attainment results','Progress results'])
    work=data.assign(_valid_a=data['attainment'].notna(),_valid_p=data['progress'].notna())
    summary=work.groupby('subject',dropna=False).agg(
        Students=('student_id','nunique'),
        **{'Attainment results':('_valid_a','sum'),'Progress results':('_valid_p','sum')}
    ).reset_index().rename(columns={'subject':'Subject'})
    return summary


def attained_grade_counts(data):
    if data.empty:return pd.DataFrame(columns=['Grade','Count','Percent'])
    valid=data.loc[data['attainment'].notna() & data['current_grade'].notna()]
    if valid.empty:return pd.DataFrame(columns=['Grade','Count','Percent'])
    c=valid['current_grade'].astype(str).value_counts()
    return pd.DataFrame({'Grade':c.index,'Count':c.values,'Percent':c.values*100/len(valid)})


def validate_overview_invariants(table, mode):
    """Cheap independent sanity checks for the output of the presentation layer."""
    if table.empty:return True
    assert 'Subject' in table.columns and 'Number' in table.columns
    assert 'KHDA grade' in table.columns
    assert 'Progress results (n)' not in table.columns or mode=='detailed'
    assert 'Grade results (n)' not in table.columns or mode=='detailed'
    assert (table['Number']>=0).all()
    return True


def focus_judgements(display, focus='All results'):
    """Keep the table and export focused on the same selected judgement bands."""
    if focus=='Weak / Acceptable':
        return display.loc[display['KHDA grade'].isin(['Weak','Acceptable'])].copy()
    if focus=='Good or above':
        return display.loc[display['KHDA grade'].isin(['Good','Very Good','Outstanding'])].copy()
    if focus=='Without judgement':
        return display.loc[~display['KHDA grade'].isin(['Weak','Acceptable','Good','Very Good','Outstanding'])].copy()
    return display.copy()


def assessment_coverage(data, baseline_first, current_first):
    """Aggregate source counts; do not expose individual student records."""
    total=len(data)
    def count(c):return int(data[c].notna().sum()) if c in data else 0
    cur=count('current_grade');base=count('baseline_grade')
    both=int((data['current_grade'].notna()&data['baseline_grade'].notna()).sum()) if total else 0
    cur_fallback=int((data['current_source'].notna()&data['current_source'].ne(current_first)).sum()) if 'current_source' in data else 0
    base_fallback=int((data['baseline_source'].notna()&data['baseline_source'].ne(baseline_first)).sum()) if 'baseline_source' in data else 0
    return {'records':total,'current_grade':cur,'baseline_grade':base,'both_grade_fields':both,
            'valid_progress':count('progress'),'current_from_fallback':cur_fallback,'baseline_from_fallback':base_fallback}


def ppm_subject_hotspots(data, limit=12):
    """Count unique students with concerns per subject, no predictive risk scoring."""
    flagged=data.loc[data['concern_count'].fillna(0)>0]
    if flagged.empty:return pd.DataFrame(columns=['Subject','Students with concerns','Concern flags'])
    result=flagged.groupby('subject').agg(
        **{'Students with concerns':('student_id','nunique'),'Concern flags':('concern_count','sum')}
    ).reset_index().rename(columns={'subject':'Subject'})
    return result.sort_values(['Students with concerns','Subject'],ascending=[False,True]).head(limit).reset_index(drop=True)
