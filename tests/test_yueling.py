import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from yueling import month_commands

# 節氣換月：小寒丑、立春寅、驚蟄卯……
GOLDEN_YUELING = {
    date(2024, 1, 5): ("甲", "子"),
    date(2024, 1, 6): ("乙", "丑"),
    date(2024, 2, 3): ("乙", "丑"),
    date(2024, 2, 4): ("丙", "寅"),
    date(2024, 3, 5): ("丁", "卯"),
    date(2025, 2, 3): ("戊", "寅"),
}


class MonthCommandTests(unittest.TestCase):
    def test_jieqi_month_boundaries_2024(self):
        commands = month_commands(date(2024, 1, 1), date(2025, 2, 10))
        by_start = {item.start: item for item in commands}
        self.assertEqual(by_start[date(2024, 1, 1)].ganzhi, "甲子")
        self.assertEqual(by_start[date(2024, 1, 1)].end_exclusive, date(2024, 1, 6))
        self.assertEqual(by_start[date(2024, 1, 6)].ganzhi, "乙丑")
        self.assertEqual(by_start[date(2024, 2, 4)].ganzhi, "丙寅")
        self.assertEqual(by_start[date(2024, 2, 4)].title, "寅月")
        self.assertEqual(by_start[date(2024, 2, 4)].branch_wuxing, "木")
        self.assertEqual(by_start[date(2025, 2, 3)].ganzhi, "戊寅")

    def test_each_day_matches_known_jieqi_months(self):
        commands = month_commands(date(2024, 1, 1), date(2025, 2, 10))

        def command_on(day: date):
            for item in commands:
                if item.start <= day < item.end_exclusive:
                    return item
            self.fail(day.isoformat())

        for day, (stem, branch) in GOLDEN_YUELING.items():
            item = command_on(day)
            self.assertEqual(item.stem, stem, day.isoformat())
            self.assertEqual(item.branch, branch, day.isoformat())

    def test_month_branches_follow_yin_to_chou(self):
        commands = month_commands(date(2024, 2, 4), date(2025, 2, 2))
        branches = "寅卯辰巳午未申酉戌亥子丑"
        self.assertEqual("".join(item.branch for item in commands), branches)


if __name__ == "__main__":
    unittest.main()
