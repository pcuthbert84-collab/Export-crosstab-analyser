"""School-approved English-only descriptor -> numeric GCSE equivalences.

Scope: progress calculations, never attainment, CAT4 or value added.
English subjects include Reading/Writing for mapped baselines and English
Language/Literature only when the *current* assessment is GCSE numeric.
This is an equivalence for calculating a comparison, not a target grade.
"""
from __future__ import annotations

ENGLISH_DESCRIPTOR_TO_GCSE = {
    'WT-': 1, 'WT': 2, 'WT+': 3, 'ME-': 3, 'ME': 4,
    'ME+': 6, 'EX-': 7, 'EX': 8, 'MA': 9,
}
ENGLISH_SUBJECTS = {'english', 'english language', 'english literature'}


def english_equivalence(baseline, current, subject):
    if baseline is None or current is None or subject is None:
        return None
    if str(subject).strip().casefold() not in ENGLISH_SUBJECTS:
        return None
    if baseline.kind != 'descriptor' or current.kind != 'gcse':
        return None
    return ENGLISH_DESCRIPTOR_TO_GCSE.get(baseline.level)
