"""DBSJP-approved global descriptor to numeric GCSE / paired GCSE equivalences.

These are PROGRESS equivalents, not an instruction to change curriculum
attainment classifications or numeric targets. They apply to any subject
whose CURRENT grade is numeric GCSE or a valid paired GCSE grade.
An exact match compares with the equivalent point; the existing high-grade
progress override remains in place until separately reviewed.
"""
from __future__ import annotations

DESCRIPTOR_TO_GCSE = {
    'WT-': 1, 'WT': 2, 'WT+': 3, 'ME-': 3, 'ME': 4,
    'ME+': 6, 'EX-': 7, 'EX': 8, 'MA': 9,
}


def baseline_equivalent(baseline, current):
    """Expected numeric destination for a descriptor baseline, if approved."""
    if baseline is None or current is None:
        return None
    if baseline.kind != 'descriptor' or current.kind not in ('gcse', 'double'):
        return None
    return DESCRIPTOR_TO_GCSE.get(baseline.level)


def paired_equivalent(descriptor):
    n = DESCRIPTOR_TO_GCSE.get(descriptor)
    return f'{n},{n}' if n is not None else None
