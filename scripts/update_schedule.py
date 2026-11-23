#!/usr/bin/env python3
"""Fetch upcoming CoderDojo Nisshin events from the connpass API and
regenerate _data/schedule.yml for the Jekyll site.

Data source: connpass API v1, series_id 5408 (CoderDojo Nisshin).
Only events starting today or later (JST) are listed, in start order.
"""
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
SERIES_ID = 5408
API_URL = "https://connpass.com/api/v1/event/"
OUTPUT_PATH = "_data/schedule.yml"


def fetch_events():
    events = []
    start = 1
    while True:
        url = (
            f"{API_URL}?series_id={SERIES_ID}&order=2&count=100&start={start}"
        )
        req = urllib.request.Request(
            url, headers={"User-Agent": "coderdojo-nisshin-schedule-bot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        batch = data.get("events", [])
        events.extend(batch)
        if len(events) >= data.get("results_available", 0) or not batch:
            break
        start += len(batch)
    return events


def yaml_scalar(value):
    """Emit a plain YAML scalar, double-quoting when necessary."""
    if value == "":
        return '""'
    needs_quote = (
        value != value.strip()
        or ": " in value
        or " #" in value
        or value[0] in "-?:,[]{}#&*!|>'\"%@`"
    )
    if needs_quote:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def main():
    now = datetime.now(JST)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    upcoming = []
    for ev in fetch_events():
        started = datetime.fromisoformat(ev["started_at"])
        if started < today_start:
            continue
        ended = datetime.fromisoformat(ev["ended_at"])
        if started.date() == ended.date():
            date_str = f"{started:%Y/%m/%d %H:%M}-{ended:%H:%M}"
        else:
            date_str = f"{started:%Y/%m/%d %H:%M}-{ended:%Y/%m/%d %H:%M}"
        text = (ev.get("place") or ev.get("address") or "").strip()
        upcoming.append(
            {"date": date_str, "link": ev["event_url"], "text": text}
        )

    upcoming.sort(key=lambda e: e["date"])

    lines = []
    for e in upcoming:
        lines.append(f"- date: {e['date']}")
        lines.append(f"  link: {e['link']}")
        lines.append(f"  text: {yaml_scalar(e['text'])}")
    content = "\n".join(lines) + ("\n" if lines else "")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {len(upcoming)} event(s) to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
