import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ganzhi import DayPillar, day_pillar, julian_day_number

GOLDEN_DAYS = {
    date(2000, 1, 1): "戊午",
    date(2001, 1, 1): "甲子",
    date(2019, 1, 27): "甲子",
    date(1986, 5, 29): "癸酉",
    date(1781, 3, 13): "壬戌",
}

KNOWN_JDN = {
    date(2000, 1, 1): 2451545,
    date(2001, 1, 1): 2451911,
    date(2019, 1, 27): 2458511,
}


class JulianDayNumberTests(unittest.TestCase):
    def test_known_noon_jdn(self):
        for d, expected in KNOWN_JDN.items():
            self.assertEqual(
                julian_day_number(d.year, d.month, d.day),
                expected,
                d.isoformat(),
            )


class GoldenDayPillarTests(unittest.TestCase):
    def test_historical_golden_dates(self):
        for d, expected in GOLDEN_DAYS.items():
            pillar = day_pillar(d)
            self.assertEqual(pillar.ganzhi, expected, d.isoformat())
            self.assertIsInstance(pillar, DayPillar)


class InvariantTests(unittest.TestCase):
    def test_consecutive_days_advance_by_one(self):
        start = date(2024, 1, 1)
        previous = day_pillar(start)
        for offset in range(1, 120):
            current_date = start + timedelta(days=offset)
            current = day_pillar(current_date)
            expected_stem_index = ( "甲乙丙丁戊己庚辛壬癸".index(previous.stem) + 1) % 10
            expected_branch_index = ( "子丑寅卯辰巳午未申酉戌亥".index(previous.branch) + 1) % 12
            self.assertEqual("甲乙丙丁戊己庚辛壬癸"[expected_stem_index], current.stem)
            self.assertEqual("子丑寅卯辰巳午未申酉戌亥"[expected_branch_index], current.branch)
            previous = current

    def test_guihai_followed_by_jiazi(self):
        day = date(2001, 1, 1)
        while day_pillar(day).ganzhi != "癸亥":
            day += timedelta(days=1)
        self.assertEqual(day_pillar(day + timedelta(days=1)).ganzhi, "甲子")

    def test_leap_day_2024_is_continuous(self):
        feb28 = day_pillar(date(2024, 2, 28))
        feb29 = day_pillar(date(2024, 2, 29))
        mar01 = day_pillar(date(2024, 3, 1))
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        self.assertEqual(stems[(stems.index(feb28.stem) + 1) % 10], feb29.stem)
        self.assertEqual(branches[(branches.index(feb28.branch) + 1) % 12], feb29.branch)
        self.assertEqual(stems[(stems.index(feb29.stem) + 1) % 10], mar01.stem)
        self.assertEqual(branches[(branches.index(feb29.branch) + 1) % 12], mar01.branch)

    def test_wuxing_follows_day_stem(self):
        mapping = {
            "甲": "木",
            "乙": "木",
            "丙": "火",
            "丁": "火",
            "戊": "土",
            "己": "土",
            "庚": "金",
            "辛": "金",
            "壬": "水",
            "癸": "水",
        }
        day = date(2024, 1, 1)
        for _ in range(60):
            pillar = day_pillar(day)
            self.assertEqual(pillar.wuxing, mapping[pillar.stem])
            day += timedelta(days=1)

    def test_wuxing_follows_day_branch(self):
        mapping = {
            "子": "水",
            "丑": "土",
            "寅": "木",
            "卯": "木",
            "辰": "土",
            "巳": "火",
            "午": "火",
            "未": "土",
            "申": "金",
            "酉": "金",
            "戌": "土",
            "亥": "水",
        }
        day = date(2024, 1, 1)
        for _ in range(60):
            pillar = day_pillar(day)
            self.assertEqual(pillar.branch_wuxing, mapping[pillar.branch])
            day += timedelta(days=1)

    def test_golden_dates_split_wuxing(self):
        self.assertEqual(day_pillar(date(2001, 1, 1)).wuxing, "木")
        self.assertEqual(day_pillar(date(2001, 1, 1)).branch_wuxing, "水")
        self.assertEqual(day_pillar(date(1986, 5, 29)).wuxing, "水")
        self.assertEqual(day_pillar(date(1986, 5, 29)).branch_wuxing, "金")


class LunarPythonSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from lunar_python import Solar
        except ImportError as exc:  # pragma: no cover - 環境缺套件時明確失敗
            raise unittest.SkipTest(
                "需要 lunar_python 才能做萬年曆全區間對照：pip install lunar_python"
            ) from exc
        cls.Solar = Solar

    def test_matches_lunar_python_day_ganzhi_2024_to_2029(self):
        day = date(2024, 1, 1)
        end = date(2029, 12, 31)
        mismatches = []
        while day <= end:
            expected = self.Solar.fromYmd(day.year, day.month, day.day).getLunar().getDayInGanZhi()
            actual = day_pillar(day).ganzhi
            if actual != expected:
                mismatches.append(f"{day.isoformat()}: {actual} != {expected}")
                if len(mismatches) >= 10:
                    break
            day += timedelta(days=1)
        self.assertEqual(mismatches, [], "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main()
