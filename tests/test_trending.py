"""热门仓库榜单的离线单元测试（不打网络）。"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trending import day_tag, parse_search_response


class DayTagTest(unittest.TestCase):
    def test_known_date(self):
        self.assertEqual(day_tag(datetime(2026, 8, 24, tzinfo=timezone.utc)), "2026-08-24")

    def test_year_boundary(self):
        self.assertEqual(day_tag(datetime(2027, 1, 1, tzinfo=timezone.utc)), "2027-01-01")


class ParseSearchResponseTest(unittest.TestCase):
    def test_parses_fields(self):
        items = [
            {
                "full_name": "o/r",
                "stargazers_count": 1234,
                "description": " desc ",
                "language": "Python",
                "html_url": "https://github.com/o/r",
            }
        ]
        out = parse_search_response(items)
        self.assertEqual(out[0]["repo"], "o/r")
        self.assertEqual(out[0]["stars"], 1234)
        self.assertEqual(out[0]["description"], "desc")
        self.assertEqual(out[0]["language"], "Python")

    def test_caps_at_ten(self):
        items = [{"full_name": f"o/r{i}", "stargazers_count": i} for i in range(15)]
        self.assertEqual(len(parse_search_response(items)), 10)

    def test_missing_description(self):
        out = parse_search_response([{"full_name": "o/r"}])
        self.assertEqual(out[0]["description"], "")
        self.assertEqual(out[0]["language"], "-")


if __name__ == "__main__":
    unittest.main()
