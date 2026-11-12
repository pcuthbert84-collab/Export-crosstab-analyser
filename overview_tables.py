"""Presentation-only helpers for streamlined assessment overview tables."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from engine import summarise, judgement, classify_attainment, parse_grade


def whole_pct(value):
    if value is None or pd.isna(value):
        return '—'
    return f"{int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%"


def grade_kind(row):
    name = str(row.get('subject', '')).lower()
    if 'btec' in name:
        return 'btec'
    if int(row.get('year', 0)) >= 12:
        return 'alevel'
    return 'auto'


def grade_sort_key(value):
    g = parse_grade(value, 'auto')
    if g is None:
        for kind in ('btec', 'alevel'):
            g = parse_grade(value, kind)
            if g is not None:
                break
    return ((g.point if g is not None else -999), str(value))


def summary_tables(data, by=('category',), method='pooled'):
    """Return presentational compact and detailed tables, without changing engine results.

    Denominators are valid subject-assessment results; Students counts distinct IDs.
    Predicted percentages classify target grades using the original subject grade set.
    """
    raw = summarise(data, by, method)
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    attainment_rows=[]; progress_rows=[]; grade_rows=[]
    groupby_arg=list(by)
    for keys, group in data.groupby(groupby_arg, dropna=False):
        if not isinstance(keys, tuple):keys=(keys,)
        labels=dict(zip(by, keys))
        valid_a=group[group['attainment'].notna()]
        valid_p=group[group['progress'].notna()]
        count_valid_a=len(valid_a)
        count_valid_p=len(valid_p)
        if count_valid_a==0 and count_valid_p==0:
            continue
        # Grade counts shown for every represented grade, not only a subset.
        frequencies=valid_a['current_grade'].astype(str).value_counts().to_dict()
        grade_columns={f'Grade {g} · n':int(n) for g,n in frequencies.items()}
        for g,n in frequencies.items():
            grade_rows.append({**labels, 'Grade':g, 'Count':int(n), 'Percent':100*n/count_valid_a if count_valid_a else None})
        predictions=[]
        for row in group.to_dict('records'):
            target = parse_grade(row.get('target_grade'),grade_kind(row))
            classification=classify_attainment(target,row.get('year')) if target is not None else None
            if classification is not None:
                predictions.append((row['subject'],classification))
        def predicted_percent(accepted):
            if not predictions:
                return None
            if method=='unweighted':
                subjects={subject for subject,_ in predictions}
                rates=[sum(c in accepted for s,c in predictions if s==subject)/sum(s==subject for s,c in predictions) for subject in subjects]
                return 100*sum(rates)/len(rates)
            return 100*sum(c in accepted for _,c in predictions)/len(predictions)
        predicted_at=predicted_percent(('At','Above'))
        predicted_above=predicted_percent(('Above',))
        match=raw
        for key, value in labels.items():match=match[match[key].eq(value)]
        if match.empty:continue
        s=match.iloc[0]
        atta={**labels,'Students with grades':valid_a.student_id.nunique(),'Grade results (n)':count_valid_a,
            '% Meeting or above':whole_pct(s['at_or_above']),'% Exceeding':whole_pct(s['above']),
            'KHDA grade':s['attainment_judgement'] or '—'}
        attainment_rows.append({**atta, **grade_columns,
            'Target-predicted at/above':whole_pct(predicted_at),'Target-predicted above':whole_pct(predicted_above),
            'Target results (n)':len(predictions)})
        prog={**labels,'Students with both grades':valid_p.student_id.nunique(),'Progress results (n)':count_valid_p,
            '% Expected or better':whole_pct(s['expected_plus']),'% Better than expected':whole_pct(s['better']),
            'KHDA grade':s['progress_judgement'] or '—'}
        progress_rows.append({**prog, 'Less · n':int(valid_p['progress'].eq('Less').sum()),
            'Expected · n':int(valid_p['progress'].eq('Expected').sum()),
            'Better · n':int(valid_p['progress'].eq('Better').sum()),
            **grade_columns, '% Met CAT4 target':whole_pct(s['met_cat4']),
            '% Met challenge target':whole_pct(s['met_cat4_75']),
            'CAT4 eligible (n)':int(s['met_cat4_n']),
            'Challenge eligible (n)':int(s['met_cat4_75_n'])})
    return pd.DataFrame(attainment_rows),pd.DataFrame(progress_rows),pd.DataFrame(grade_rows)


def compact_table(table, by, mode):
    cols=list(by)+(['Students with grades','Grade results (n)','% Meeting or above','% Exceeding','KHDA grade']
        if mode=='attainment' else ['Students with both grades','Progress results (n)','% Expected or better','% Better than expected','KHDA grade'])
    return table.reindex(columns=cols)


def detail_table(table, by, mode):
    core=list(compact_table(table,by,mode).columns)
    extra=[c for c in table.columns if c not in core]
    return table[core+extra]
