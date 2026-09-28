"""日柱天干地支：兩套獨立算法必須一致，否則拒絕回傳。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

STEM_WUXING = {
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

# 地支本氣五行：亥子水、寅卯木、巳午火、申酉金、辰戌丑未土
BRANCH_WUXING = {
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

# 2001-01-01 為甲子；該日正午儒略日 2451911 ≡ 1 (mod 60)
_JIAZI_ORDINAL_ANCHOR = date(2001, 1, 1)


class GanzhiMismatchError(RuntimeError):
    """公曆序日與儒略日兩套算法結果不一致。"""


@dataclass(frozen=True)
class DayPillar:
    stem: str
    branch: str
    wuxing: str
    branch_wuxing: str

    @property
    def ganzhi(self) -> str:
        return f"{self.stem}{self.branch}"


def julian_day_number(year: int, month: int, day: int) -> int:
    """格里曆日期對應的正午儒略日數（Meeus 整數公式）。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return (
        day
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )


def _from_ordinal(d: date) -> tuple[str, str]:
    idx = (d.toordinal() - _JIAZI_ORDINAL_ANCHOR.toordinal()) % 60
    return STEMS[idx % 10], BRANCHES[idx % 12]


def _from_jdn(d: date) -> tuple[str, str]:
    jdn = julian_day_number(d.year, d.month, d.day)
    stem_index = (jdn - 1) % 10
    branch_index = (jdn + 1) % 12
    return STEMS[stem_index], BRANCHES[branch_index]


def day_pillar(d: date) -> DayPillar:
    """回傳該公曆日的日柱。兩套算法不一致時拋錯，不產出結果。"""
    ordinal_pair = _from_ordinal(d)
    jdn_pair = _from_jdn(d)
    if ordinal_pair != jdn_pair:
        raise GanzhiMismatchError(
            f"{d.isoformat()} 干支不一致：序日={ordinal_pair[0]}{ordinal_pair[1]} "
            f"儒略日={jdn_pair[0]}{jdn_pair[1]}"
        )
    stem, branch = ordinal_pair
    return DayPillar(
        stem=stem,
        branch=branch,
        wuxing=STEM_WUXING[stem],
        branch_wuxing=BRANCH_WUXING[branch],
    )
