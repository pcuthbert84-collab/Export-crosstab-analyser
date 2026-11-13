"""Optional, session-only cross-subject progress baseline mapping.

A mapping applies to a current (enrolled year, subject) and searches the immediately
preceding uploaded year for that student's selected source subject(s). It never
modifies attainment, targets, grade distribution, or already comparable progress.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import replace
import pandas as pd
from engine import Grade, parse_grade, select_grade, progress
from science_grade_conversions import science_equivalence


def grade_kind(subject: str, year: int) -> str:
    return 'btec' if 'btec' in str(subject).lower() else 'alevel' if int(year) >= 12 else 'auto'


def mapping_candidates(records: pd.DataFrame, baseline: str, fallback: str | None = None) -> list[dict]:
    """Return current-year subjects with possible preceding-year sources.

    Only display choices when both year groups have been uploaded; do not guess
    mappings or silently equate different subjects.
    """
    if records.empty:
        return []
    results=[]
    for year in sorted(records['year'].dropna().astype(int).unique()):
        earlier=records[records['year']==year-1]
        now=records[records['year']==year]
        if earlier.empty or now.empty:
            continue
        earlier_names=sorted(earlier['subject'].dropna().astype(str).unique(),key=str.lower)
        for subject in sorted(now['subject'].dropna().astype(str).unique(),key=str.lower):
            current=now[now['subject']==subject]
            if current.empty:
                continue
            sources=[]
            for name in earlier_names:
                previous=earlier[earlier['subject']==name]
                if previous.empty:continue
                # Offer only source subjects where any usable baseline grade exists.
                if any(select_grade(r,baseline,fallback,grade_kind(name,year-1))[0] for r in previous.to_dict('records')):
                    sources.append(name)
            if not sources:continue
            previous_same=earlier[earlier['subject']==subject]
            ids_current=set(current['student_id'].astype(str))
            ids_prior=set(earlier['student_id'].astype(str))
            overlaps=len(ids_current & ids_prior)
            if overlaps==0:continue
            same_grade_ids={str(r['student_id']) for r in previous_same.to_dict('records') if select_grade(r,baseline,fallback,grade_kind(subject,year-1))[0]}
            missing=len(ids_current & ids_prior - same_grade_ids)
            # Keep all possible subject candidates, but raise missing previous-subject matches first.
            results.append({'year':year,'subject':subject,'previous_year':year-1,
                            'sources':sources,'matched_students':overlaps,'missing_same_subject':missing})
    return results


def _baseline_equivalent_point(grade: Grade, current: Grade, enrolled_prior_year: int, subject: str | None = None) -> float | None:
    """Map an earlier grade to a current-grade-scale expected destination.

    This is intentionally conservative: cross-system transitions are only
    approved for KS3 ME -> GCSE4 and ME+ -> GCSE6. Unknown equivalences are not
    inferred from provisional numeric-point values.
    """
    approved_science = science_equivalence(grade, current, subject)
    if approved_science is not None:
        return float(approved_science)
    if grade.kind==current.kind:
        if grade.kind=='descriptor' and grade.curriculum_year is not None and grade.curriculum_year!=enrolled_prior_year:
            # The different curriculum-year prefix needs a separate approved mapping.
            return None
        return grade.point
    if grade.kind=='descriptor' and current.kind=='gcse':
        return {'ME':4.0,'ME+':6.0}.get(grade.level)
    return None


def _mapped_progress(current: Grade, baseline_point: float):
    # preserve approved high-achievement classification even with a decline
    if current.kind=='gcse' and current.point>=7:return 'Better'
    if current.kind=='descriptor' and current.level in ('EX-','EX','MA'):return 'Better'
    if current.kind=='double' and current.pair>=(7,6):return 'Better'
    if current.kind=='alevel' and current.level in ('A','A*'):return 'Better'
    if current.point>baseline_point:return 'Better'
    if current.point<baseline_point:return 'Less'
    return 'Expected'


def apply_subject_mappings(
    calculated: pd.DataFrame, records: pd.DataFrame,
    mappings: dict[tuple[int,str],list[str]], baseline: str,
    fallback: str | None = None,
) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Fill missing comparable progress using explicit previous-year mappings.

    Returns updated calculated rows and a per-row audit dataframe. Each eligible
    student contributes at most one current subject progress outcome. If selected
    source grades are absent, average the available valid mapped sources only,
    and disclose exactly which were used.
    """
    updated=calculated.copy()
    updated['progress_baseline_mapping'] = None
    updated['progress_baseline_sources'] = None
    audit=[]
    if not mappings or records.empty or updated.empty:
        return updated,pd.DataFrame(audit)
    lookup=defaultdict(list)
    for r in records.to_dict('records'):
        lookup[(str(r['student_id']),int(r['year']),str(r['subject']))].append(r)
    for idx,row in updated.iterrows():
        year=int(row['year']);subject=str(row['subject']);student=str(row['student_id'])
        selected=mappings.get((year,subject),[])
        if not selected or row.get('progress') in ('Less','Expected','Better'):
            continue
        # Never overwrite a legitimate same-subject baseline with a different subject.
        if pd.notna(row.get('baseline_grade')):
            continue
        current=parse_grade(row.get('current_grade'),grade_kind(subject,year))
        if not current:continue
        points=[];used=[];unsupported=[]
        for source_subject in selected:
            candidates=lookup.get((student,year-1,source_subject),[])
            if len(candidates)!=1:
                if len(candidates)>1: unsupported.append(f'{source_subject}: duplicate rows')
                continue
            g,field=select_grade(candidates[0],baseline,fallback,grade_kind(source_subject,year-1))
            if not g:continue
            equivalent=_baseline_equivalent_point(g,current,year-1,subject=subject)
            if equivalent is None:
                unsupported.append(f'{source_subject}: {g.raw} needs approved conversion')
                continue
            points.append(equivalent)
            used.append((source_subject,g.raw,field))
        if unsupported:
            audit.append({'student_id':student,'year':year,'subject':subject,'status':'Needs conversion',
                          'details':'; '.join(unsupported)})
            continue
        if not points:
            continue
        mean=sum(points)/len(points)
        result=_mapped_progress(current,mean)
        oldgrade='Average: '+', '.join(f'{s} {g}' for s,g,_ in used) if len(used)>1 else f'{used[0][0]}: {used[0][1]}'
        updated.at[idx,'baseline_grade']=oldgrade
        updated.at[idx,'baseline_source']=f'Year {year-1} · mapped subject(s)'
        updated.at[idx,'progress']=result
        updated.at[idx,'progress_baseline_mapping']='Average of mapped subjects' if len(used)>1 else 'Mapped single subject'
        updated.at[idx,'progress_baseline_sources']='; '.join(f'{s} ({g}, {field})' for s,g,field in used)
        # Retain existing grade-decline and VA calculations rather than comparing
        # the new baseline mean as a literal original grade.
        oldconcerns=[x.strip() for x in str(row.get('concerns') or '').split(',') if x.strip()]
        oldconcerns=[x for x in oldconcerns if x!='Less progress']
        if result=='Less':oldconcerns.append('Less progress')
        updated.at[idx,'concerns']=', '.join(oldconcerns)
        updated.at[idx,'concern_count']=len(oldconcerns)
        audit.append({'student_id':student,'year':year,'subject':subject,'status':'Mapped',
                      'details':f'{oldgrade} → {current.raw} = {result}'})
    return updated,pd.DataFrame(audit)
