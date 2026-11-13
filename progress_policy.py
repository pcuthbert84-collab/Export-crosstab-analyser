"""School-approved no-transition and within-course measurement metadata.

Do not derive any unsupported qualification conversion or baseline.
"""
from __future__ import annotations
import pandas as pd
from transition_library import normalise_subject


def apply_reporting_policy(calculated: pd.DataFrame, library: dict) -> pd.DataFrame:
    out = calculated.copy()
    out['Progress basis'] = 'Prior assessment'
    for policy in library.get('within_course_policies', []):
        matched = out['year'].eq(int(policy['year'])) & out['subject'].map(normalise_subject).eq(normalise_subject(policy['subject']))
        if policy.get('status') != 'approved':
            continue
        out.loc[matched & out['progress'].notna(), 'Progress basis'] = 'Within-course progress'
        out.loc[matched & out['progress'].isna(), 'Progress basis'] = 'Within-course: awaiting comparable assessments'
    for policy in library.get('pending_reviews', []):
        if policy.get('year') is None: continue
        matched = out['year'].eq(int(policy['year'])) & out['subject'].map(normalise_subject).eq(normalise_subject(policy['subject']))
        out.loc[matched & out['progress'].isna(), 'Progress basis'] = 'Pending approved conversion / review'
    return out
