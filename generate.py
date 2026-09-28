"""依日干五行產出五份 ICS 訂閱日曆。兩套干支算法不一致時會中止、不寫檔。"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from ganzhi import DayPillar, day_pillar

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


def _vevent(d: date, pillar: DayPillar, stamp: str) -> list[str]:
    next_day = d + timedelta(days=1)
    return [
        "BEGIN:VEVENT",
        f"UID:ganzhi-{d.strftime('%Y%m%d')}-{pillar.wuxing}@{DOMAIN}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}",
        f"SUMMARY:{_ics_text(pillar.ganzhi)}",
        "TRANSP:TRANSPARENT",
        "STATUS:CONFIRMED",
        "END:VEVENT",
    ]


def build_calendar(name: str, color: str, events: list[tuple[date, DayPillar]], stamp: str) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ics_text(name)}",
        f"X-APPLE-CALENDAR-COLOR:{color}",
    ]
    for d, pillar in events:
        lines.extend(_vevent(d, pillar, stamp))
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def daterange(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def generate(start: date, end: date, output_dirs: list[Path]) -> dict[str, int]:
    grouped: dict[str, list[tuple[date, DayPillar]]] = {key: [] for key in WUXING_CALENDARS}
    for day in daterange(start, end):
        pillar = day_pillar(day)
        grouped[pillar.wuxing].append((day, pillar))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    counts = {key: len(items) for key, items in grouped.items()}

    for output_dir in output_dirs:
        output_dir.mkdir(parents=True, exist_ok=True)
        for wuxing, meta in WUXING_CALENDARS.items():
            ics = build_calendar(meta["name"], meta["color"], grouped[wuxing], stamp)
            (output_dir / meta["filename"]).write_bytes(ics.encode("utf-8"))
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="產生天干地支五行 ICS 日曆")
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
    print(f"已產出 {start.isoformat()} 至 {end.isoformat()}，共 {total} 天：")
    for wuxing, meta in WUXING_CALENDARS.items():
        print(f"  {meta['name']} ({meta['filename']}): {counts[wuxing]} 筆")
    print(f"輸出目錄：{args.out} 與 {public_calendars}")


if __name__ == "__main__":
    main()
