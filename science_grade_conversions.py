"""School-approved Science-only KS3 descriptor equivalences for progress.

No effect on attainment, CAT4 target achievement or value added. The two
components of the reference Combined Science pair are identical, as agreed.
Grades with a curriculum-year prefix retain their descriptor label for this
specific approved conversion; other curriculum-year progress rules are unchanged.
"""
from __future__ import annotations

SCIENCE_DESCRIPTOR_TO_GCSE = {
    'WT-': 1, 'WT': 2, 'WT+': 3, 'ME-': 3, 'ME': 4,
    'ME+': 6, 'EX-': 7, 'EX': 8, 'MA': 9,
}
SCIENCE_SUBJECTS = {
    'science', 'combined science', 'science - combined',
    'biology', 'chemistry', 'physics',
    'science - biology', 'science - chemistry', 'science - physics',
}


def science_equivalence(baseline, current, subject):
    """Return an approved expected GCSE grade point, or None.

    A Combined Science grade compares the *mean* of its two components to
    the approved (n,n) equivalent, with high-achievement override preserved.
    Only applies to descriptor -> GCSE or valid paired GCSE, and Science subjects.
    """
    if baseline is None or current is None or subject is None:
        return None
    if str(subject).strip().casefold() not in SCIENCE_SUBJECTS:
        return None
    if baseline.kind != 'descriptor' or current.kind not in ('gcse', 'double'):
        return None
    return SCIENCE_DESCRIPTOR_TO_GCSE.get(baseline.level)


def paired_science_equivalent(descriptor):
    """Documented paired reference grade for Combined Science (e.g. '6,6')."""
    point = SCIENCE_DESCRIPTOR_TO_GCSE.get(descriptor)
    return f'{point},{point}' if point is not None else None
