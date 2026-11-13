"""Privacy-preserving aggregate progress eligibility audit."""
import pandas as pd


def progress_coverage(calculated: pd.DataFrame, by=('year','category')) -> pd.DataFrame:
    if calculated.empty:
        return pd.DataFrame()
    rows=[]
    for group,part in calculated.groupby(list(by),dropna=False):
        vals=group if isinstance(group,tuple) else (group,)
        current=part.loc[part['current_grade'].notna()]
        both=current.loc[current['baseline_grade'].notna()]
        valid=current.loc[current['progress'].notna()]
        unresolved=both.loc[both['progress'].isna()]
        mapped=valid.loc[valid.get('progress_baseline_mapping',pd.Series(None,index=valid.index)).notna()]
        rows.append({**dict(zip(by,vals)),
            'Students with current grade':int(current.student_id.nunique()),
            'Students with baseline and current':int(both.student_id.nunique()),
            'Progress classified':int(valid.student_id.nunique()),
            'Current grade, baseline missing':int(current.loc[current.baseline_grade.isna(),'student_id'].nunique()),
            'Grade conversion not approved':int(unresolved.student_id.nunique()),
            'From optional mapping':int(mapped.student_id.nunique()),
            '% progress coverage':round(100*valid.student_id.nunique()/current.student_id.nunique(),1) if current.student_id.nunique() else None,
        })
    return pd.DataFrame(rows)
