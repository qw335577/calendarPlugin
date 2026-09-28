"""節氣月令：以節交接當天 0:00 換月（萬年曆慣例，不是交節時刻）。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from lunar_python import Solar

from ganzhi import BRANCH_WUXING


@dataclass(frozen=True)
class MonthCommand:
    start: date
    end_exclusive: date
    stem: str
    branch: str
    branch_wuxing: str

    @property
    def ganzhi(self) -> str:
        return f"{self.stem}{self.branch}"

    @property
    def title(self) -> str:
        return f"{self.branch}月"


def _month_gz(d: date) -> tuple[str, str]:
    lunar = Solar.fromYmd(d.year, d.month, d.day).getLunar()
    return lunar.getMonthGan(), lunar.getMonthZhi()


def month_commands(start: date, end: date) -> list[MonthCommand]:
    """產出 [start, end] 內每一段月令。首段若跨出起始日，會裁到 start。"""
    if end < start:
        return []

    commands: list[MonthCommand] = []
    period_start = start
    stem, branch = _month_gz(start)
    day = start + timedelta(days=1)
    last = end + timedelta(days=1)

    while day <= last:
        if day <= end:
            next_stem, next_branch = _month_gz(day)
        else:
            next_stem, next_branch = ("", "")
        changed = day > end or (next_stem, next_branch) != (stem, branch)
        if changed:
            commands.append(
                MonthCommand(
                    start=period_start,
                    end_exclusive=day,
                    stem=stem,
                    branch=branch,
                    branch_wuxing=BRANCH_WUXING[branch],
                )
            )
            if day > end:
                break
            period_start = day
            stem, branch = next_stem, next_branch
        day += timedelta(days=1)
    return commands
