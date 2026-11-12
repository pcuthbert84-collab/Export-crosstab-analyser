"""Regression tests for the dashboard phase filter."""
import unittest
import pandas as pd
from engine import parse_dcpro


class PhaseFilterTests(unittest.TestCase):
    def test_year_to_phase_mapping(self):
        frame = pd.DataFrame({"Student ID": ["TEST01"], "Mathematics, DP1 CPL / AG 2026/27": ["6"]})
        for year, expected in [(1,2),(6,2),(7,3),(11,3),(12,4),(13,4)]:
            with self.subTest(year=year):
                rows = parse_dcpro(frame, year)
                self.assertEqual(int(rows.iloc[0]["phase"]), expected)

    def test_selected_phases_limit_rows(self):
        frame = pd.DataFrame({"Student ID": ["TEST01"], "Mathematics, DP1 CPL / AG 2026/27": ["6"]})
        data = pd.concat([parse_dcpro(frame, y) for y in (5,8,12)], ignore_index=True)
        self.assertEqual(set(data.loc[data.phase.isin([2,4]), "year"]), {5,12})
        self.assertTrue(data.loc[data.phase.isin([1])].empty)

if __name__ == "__main__":
    unittest.main()
