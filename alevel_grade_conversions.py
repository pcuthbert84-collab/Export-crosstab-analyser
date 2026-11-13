"""Approved GCSE -> A Level expected-progress destinations for all A Levels.

This policy is solely for progress, not attainment, target or value-added.
The GCSE baseline and A Level current grade must belong to the same student.
"""

GCSE_TO_ALEVEL = {
    1: 'U',
    2: 'E',
    3: 'D',
    4: 'C',
    5: 'C',
    6: 'B',
    7: 'A',
    8: 'A',
    9: 'A*',
}

# Match the existing engine's A Level grade-point scale.
ALEVEL_POINTS = {'U': 0, 'E': 2, 'D': 4, 'C': 5, 'B': 6, 'A': 7, 'A*': 9}


def gcse_to_alevel_expected(baseline, current):
    """Return the approved A Level-scale expectation, or None if unrelated."""
    if baseline is None or current is None:
        return None
    if baseline.kind != 'gcse' or current.kind != 'alevel':
        return None
    # GCSE U has no approved GCSE-to-A Level destination; do not guess.
    if baseline.level == 'U':
        return None
    try:
        gcse_grade = int(baseline.level)
    except (ValueError, TypeError):
        return None
    expected_grade = GCSE_TO_ALEVEL.get(gcse_grade)
    return ALEVEL_POINTS.get(expected_grade)
