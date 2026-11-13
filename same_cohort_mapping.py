"""Optional mappings within the same *current cohort export*.

Exports may contain last year's subject grades (DP3/Exam) under a different
subject heading. Match student ID AND enrolled year, never a different cohort's
current Year 6 workbook to the Year 7 cohort. No data is persisted.
"""
from __future__ import annotations
from collections import defaultdict
import pandas as pd
from engine import parse_grade, select_grade
from progress_subject_mapping import grade_kind, _baseline_equivalent_point, _mapped_progress


def same_cohort_candidates(records: pd.DataFrame, calculated: pd.DataFrame,
                           baseline: str, fallback: str | None = None,
                           approved_library: dict | None = None) -> list[dict]:
    if records.empty or calculated.empty:
        return []
    results = []
    from transition_library import find_rule, is_explicitly_unmapped
    current_rows = calculated.loc[
        calculated['current_grade'].notna() & calculated['progress'].isna() & calculated['baseline_grade'].isna(),
        ['student_id','year','subject','category']
    ].copy()
    if current_rows.empty:
        return []
    # Only offer prior-year source subjects in the same reporting family.
    prior = records.loc[:, ['student_id','year','subject','category',
                            *[c for c in (baseline,fallback) if c and c!='None' and c in records.columns]]].copy()
    prior['has_baseline'] = prior.apply(lambda row: select_grade(
        row, baseline, fallback, grade_kind(str(row['subject']), int(row['year'])))[0] is not None,
        axis=1)
    prior = prior[prior['has_baseline']]
    if prior.empty:
        return []
    for (year, subject, category), group in current_rows.groupby(['year','subject','category']):
        if approved_library and is_explicitly_unmapped(approved_library, year, subject):
            continue
        ids = set(group.student_id.astype(str))
        sources = []
        p = prior.loc[prior.year.eq(year) & prior.category.eq(category) & prior.subject.ne(subject)]
        # Explicitly approved subject transitions may cross reporting categories
        # (e.g. ICT current vs Computing prior). General suggestions still
        # require the same subject category to avoid misleading matches.
        rule = next((r for r in (approved_library or {}).get('rules',[])
                     if r.get('status')=='approved' and r.get('to_year')==int(year)
                     and r.get('source_scope')=='same_cohort_prior_assessment'
                     and str(r.get('current_subject','')).casefold().strip()==str(subject).casefold().strip()), None)
        if rule:
            approved_sources={s.casefold().strip() for s in rule['source_subjects']}
            approved_prior=prior.loc[prior.year.eq(year) & prior.subject.astype(str).str.casefold().str.strip().isin(approved_sources)]
            p=pd.concat([p,approved_prior],ignore_index=True).drop_duplicates(subset=['student_id','year','subject'])
        for source, candidate in p.groupby('subject'):
            matched = len(ids & set(candidate.student_id.astype(str)))
            if matched >= 3:
                sources.append({'subject':str(source),'students':matched})
        if sources:
            results.append({'year':int(year),'subject':str(subject),'category':str(category),
                            'missing':len(group),'sources':sorted(sources,key=lambda x:-x['students'])})
    return sorted(results, key=lambda item:(-item['missing'],item['year'],item['subject']))


def apply_same_cohort_mappings(calculated: pd.DataFrame, records: pd.DataFrame,
                               mappings: dict[tuple[int,str],list[str]],
                               baseline: str, fallback: str | None = None):
    updated = calculated.copy()
    if 'progress_baseline_mapping' not in updated.columns:
        updated['progress_baseline_mapping'] = None
    if 'progress_baseline_sources' not in updated.columns:
        updated['progress_baseline_sources'] = None
    audit=[]
    if updated.empty or records.empty or not mappings:
        return updated, pd.DataFrame(audit)
    lookup=defaultdict(list)
    for r in records.to_dict('records'):
        lookup[(str(r['student_id']),int(r['year']),str(r['subject']))].append(r)
    for idx,r in updated.iterrows():
        year=int(r['year']); sub=str(r['subject']); sid=str(r['student_id'])
        selected=mappings.get((year,sub),[])
        if not selected or pd.notna(r.get('baseline_grade')) or pd.notna(r.get('progress')):
            continue
        current=parse_grade(r.get('current_grade'),grade_kind(sub,year))
        if current is None:
            continue
        points=[]; descriptions=[]; missing=[]; unsupported=[]
        for source in selected:
            candidates=lookup.get((sid,year,source),[])
            if len(candidates)>1:
                unsupported.append(f'{source}: duplicate source rows')
                continue
            if not candidates:
                missing.append(source)
                continue
            grade,field=select_grade(candidates[0],baseline,fallback,grade_kind(source,year))
            if grade is None:
                missing.append(source)
                continue
            equivalent=_baseline_equivalent_point(grade,current,year-1,subject=sub)
            if equivalent is None:
                unsupported.append(f'{source}: {grade.raw} lacks approved conversion')
                continue
            points.append(equivalent)
            descriptions.append(f'{source}: {grade.raw} ({field})')
        if unsupported:
            audit.append({'year':year,'subject':sub,'status':'Needs approved conversion','count':1})
            continue
        if not points:
            audit.append({'year':year,'subject':sub,'status':'No selected source grade','count':1})
            continue
        mean=sum(points)/len(points)
        result=_mapped_progress(current,mean)
        updated.at[idx,'progress']=result
        updated.at[idx,'baseline_grade']='Mean of mapped grades' if len(points)>1 else descriptions[0].split(' (')[0]
        updated.at[idx,'baseline_source']=f'Same-cohort prior assessment ({baseline}; fallback {fallback or "none"})'
        updated.at[idx,'progress_baseline_mapping']='Same-cohort mapped subject'
        updated.at[idx,'progress_baseline_sources']='; '.join(descriptions)
        concerns=[s.strip() for s in str(r.get('concerns') or '').split(',') if s.strip()]
        if result=='Less' and 'Less progress' not in concerns:
            concerns.append('Less progress')
        updated.at[idx,'concerns']=', '.join(concerns)
        updated.at[idx,'concern_count']=len(concerns)
        audit.append({'year':year,'subject':sub,'status':'Mapped','count':1})
    return updated,pd.DataFrame(audit)
