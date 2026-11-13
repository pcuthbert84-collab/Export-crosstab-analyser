"""DBSJP approved prior ICT descriptor -> BTEC IT grade equivalences.

Scope: BTEC IT progress ONLY. Not a universal GCSE/BTEC conversion,
not an attainment/target/value-added rule, and not a subject mapping.
"""
from __future__ import annotations

ICT_TO_BTEC = {
    'WT-': 'FAIL', 'WT': 'FAIL', 'WT+': 'FAIL', 'ME-': 'FAIL',
    'ME': 'PASS', 'ME+': 'MERIT', 'EX-': 'DISTINCTION',
    'EX': 'DISTINCTION', 'MA': 'DISTINCTION*',
}
BTEC_RANK = {'U':0, 'FAIL':1, 'PASS':2, 'MERIT':3, 'DISTINCTION':4, 'DISTINCTION*':5}


def expected_btec_level(baseline, current, subject):
    if baseline is None or current is None:
        return None
    if str(subject).strip().casefold() != 'btec it':
        return None
    if baseline.kind != 'descriptor' or current.kind != 'btec':
        return None
    return ICT_TO_BTEC.get(baseline.level)


def classify_btec_progress(expected_level, current):
    if expected_level not in BTEC_RANK or current is None or current.kind != 'btec':
        return None
    actual = BTEC_RANK.get(current.level)
    if actual is None:
        return None
    target = BTEC_RANK[expected_level]
    return 'Better' if actual > target else 'Less' if actual < target else 'Expected'
