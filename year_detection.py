"""Conservative year-group suggestions from a DCPro workbook (no student data stored)."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import pandas as pd

# Require the year at the beginning of a class code, not a number inside a
# teacher code, group number or academic-year string (2026/27).
_CLASS_YEAR = re.compile(r'^\s*(?:Y(?:EAR)?\s*)?(1[0-3]|[1-9])(?=\s|[A-Za-z]|[-_/]|$)', re.I)
_FILENAME_YEAR = re.compile(r'(?<![A-Za-z0-9])(?:year|yr|y)\s*[-_. ]*\s*(1[0-3]|[1-9])(?!\d)', re.I)
_YEAR_VALUE = re.compile(r'^\s*(?:Y(?:EAR)?\s*)?(1[0-3]|[1-9])\s*$', re.I)
_CY_GRADE = re.compile(r'^\s*Y\s*(1[0-3]|[1-9])\s*(?:WT|ME|EX|MA)', re.I)

@dataclass(frozen=True)
class YearSuggestion:
    year: int | None
    source: str
    confidence: str
    note: str


def suggest_year(filename: str, sheets: list[tuple[str, pd.DataFrame]]) -> YearSuggestion:
    """Use repeated class codes first; a clear mismatch must be confirmed manually.

    Only take a small bounded sample of nonblank cells; never return row values.
    """
    class_votes: Counter[int] = Counter()
    for _, df in sheets:
        class_cols = [c for c in df.columns if re.search(r',\s*class\s*$', str(c), re.I)]
        for col in class_cols:
            for value in df[col].dropna().head(60):
                match = _CLASS_YEAR.match(str(value))
                if match:
                    class_votes[int(match.group(1))] += 1
    if class_votes:
        ranked = class_votes.most_common(2)
        best, n = ranked[0]
        total = sum(class_votes.values())
        # An overwhelming agreement among independent class codes is reliable.
        if n >= 3 and n / total >= 0.85:
            return YearSuggestion(best, 'Class codes', 'high',
                f'Found Year {best} in {n:,} of {total:,} recognised class codes. Please confirm.')
        return YearSuggestion(None, 'Class codes', 'ambiguous',
            'Different year groups appear in the class codes. Select the correct year manually.')

    # Fall back to explicit year fields. Do not treat a school year e.g. 2026/27 as the pupil year.
    field_votes: Counter[int] = Counter()
    for _, df in sheets:
        cols = [c for c in df.columns if str(c).strip().lower() in ('year','year group','yeargroup','school year group')]
        for col in cols:
            for v in df[col].dropna().head(120):
                m = _YEAR_VALUE.fullmatch(str(v))
                if m:field_votes[int(m.group(1))] += 1
    if field_votes:
        ranked = field_votes.most_common(2)
        top, n = ranked[0]
        if n >= 2 and n / sum(field_votes.values()) >= 0.9:
            return YearSuggestion(top, 'Year-group column', 'high',f'Year {top} is the consistent year-group value. Please confirm.')
        return YearSuggestion(None,'Year-group column','ambiguous','Several year groups found. Select the correct year manually.')

    # Filename / worksheet title is a weaker hint.
    title_votes = set()
    for name in [Path(filename).stem] + [sheet for sheet,_ in sheets]:
        matches = _FILENAME_YEAR.findall(str(name))
        title_votes.update(int(m) for m in matches)
    if len(title_votes) == 1:
        yr = next(iter(title_votes))
        return YearSuggestion(yr, 'Filename or worksheet', 'medium',
            f'Year {yr} appears in a file or sheet name. Please confirm.')
    if len(title_votes)>1:
        return YearSuggestion(None,'Filename or worksheet','ambiguous',
            'Multiple years appear in file or sheet names. Choose manually.')

    # Year-prefixed curriculum grades may reflect other curriculum years, so don't
    # guess from these without an independent enrollment signal.
    return YearSuggestion(None,'No reliable year evidence','unknown',
        'Could not identify the student year group. Please select it before analysis.')
