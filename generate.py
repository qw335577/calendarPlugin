"""依天干、日支、月令各自的五行產出五份 ICS。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from ganzhi import day_pillar
from yueling import month_commands

WUXING_CALENDARS = {
    "木": {
        "filename": "mu.ics",
        "name": "日柱·木",
        "color": "#2E7D32",
    },
    "火": {
        "filename": "huo.ics",
        "name": "日柱·火",
        "color": "#C62828",
    },
    "土": {
        "filename": "tu.ics",
        "name": "日柱·土",
        "color": "#F9A825",
    },
    "金": {
        "filename": "jin.ics",
        "name": "日柱·金",
        "color": "#C9A227",
    },
    "水": {
        "filename": "shui.ics",
        "name": "日柱·水",
        "color": "#1565C0",
    },
}

PRODID = "-//ganzhi-calendar//NONSGML 日柱//ZH"
DOMAIN = "ganzhi-calendar.local"


@dataclass(frozen=True)
class CalendarEvent:
    start: date
    end_exclusive: date
    title: str
    uid: str
    description: str
    wuxing: str


def _fold(line: str) -> str:
    """RFC 5545：每行不超過 75 個八位元，續行以空白開頭。"""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts: list[bytes] = []
    limit = 75
    while raw:
        chunk = raw[:limit]
        while chunk and (chunk[-1] & 0xC0) == 0x80:
            chunk = chunk[:-1]
        parts.append(chunk)
        raw = raw[len(chunk) :]
        limit = 74
    folded = parts[0]
    for part in parts[1:]:
        folded += b"\r\n " + part
    return folded.decode("utf-8")


def _ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _vevent(event: CalendarEvent, stamp: str) -> list[str]:
    return [
        "BEGIN:VEVENT",
        f"UID:{event.uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{event.start.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{event.end_exclusive.strftime('%Y%m%d')}",
        f"SUMMARY:{_ics_text(event.title)}",
        f"DESCRIPTION:{_ics_text(event.description)}",
        "TRANSP:TRANSPARENT",
        "STATUS:CONFIRMED",
        "END:VEVENT",
    ]


def build_calendar(name: str, color: str, events: list[CalendarEvent], stamp: str) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ics_text(name)}",
        f"X-APPLE-CALENDAR-COLOR:{color}",
    ]
    for event in events:
        lines.extend(_vevent(event, stamp))
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def daterange(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def collect_events(start: date, end: date) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []
    for day in daterange(start, end):
        pillar = day_pillar(day)
        next_day = day + timedelta(days=1)
        stamp = day.strftime("%Y%m%d")
        events.append(
            CalendarEvent(
                start=day,
                end_exclusive=next_day,
                title=pillar.stem,
                uid=f"ganzhi-{stamp}-gan@{DOMAIN}",
                description="天干",
                wuxing=pillar.wuxing,
            )
        )
        events.append(
            CalendarEvent(
                start=day,
                end_exclusive=next_day,
                title=pillar.branch,
                uid=f"ganzhi-{stamp}-zhi@{DOMAIN}",
                description="地支",
                wuxing=pillar.branch_wuxing,
            )
        )
    for command in month_commands(start, end):
        events.append(
            CalendarEvent(
                start=command.start,
                end_exclusive=command.end_exclusive,
                title=command.title,
                uid=f"yueling-{command.start.strftime('%Y%m%d')}-{command.branch}@{DOMAIN}",
                description=f"月令 {command.ganzhi}",
                wuxing=command.branch_wuxing,
            )
        )
    return events


def generate(start: date, end: date, output_dirs: list[Path]) -> dict[str, int]:
    grouped: dict[str, list[CalendarEvent]] = {key: [] for key in WUXING_CALENDARS}
    for event in collect_events(start, end):
        grouped[event.wuxing].append(event)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    counts = {key: len(items) for key, items in grouped.items()}

    for output_dir in output_dirs:
        output_dir.mkdir(parents=True, exist_ok=True)
        for wuxing, meta in WUXING_CALENDARS.items():
            ics = build_calendar(meta["name"], meta["color"], grouped[wuxing], stamp)
            (output_dir / meta["filename"]).write_bytes(ics.encode("utf-8"))
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="產生天干地支與月令 ICS 日曆")
    parser.add_argument("--start-year", type=int, default=2024)
    parser.add_argument("--end-year", type=int, default=2029)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("calendars"),
        help="主要輸出目錄",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.end_year < args.start_year:
        raise SystemExit("結束年不可早於起始年")

    start = date(args.start_year, 1, 1)
    end = date(args.end_year, 12, 31)
    public_calendars = Path("public") / "calendars"
    counts = generate(start, end, [args.out, public_calendars])

    total = sum(counts.values())
    print(f"已產出 {start.isoformat()} 至 {end.isoformat()}，共 {total} 筆：")
    for wuxing, meta in WUXING_CALENDARS.items():
        print(f"  {meta['name']} ({meta['filename']}): {counts[wuxing]} 筆")
    print(f"輸出目錄：{args.out} 與 {public_calendars}")


if __name__ == "__main__":
    main()
