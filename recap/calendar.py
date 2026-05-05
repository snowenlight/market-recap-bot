from __future__ import annotations

import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ET_TZ = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
USER_AGENT = (
    "market-recap-bot/0.1 "
    "(+https://github.com/snowenlight/market-recap-bot)"
)


@dataclass(frozen=True)
class CalendarEvent:
    when_et: datetime | None  # None when the time is unparseable
    time_label: str  # display label: "08:30", "終日", "未定"
    country: str
    impact: str
    title: str
    forecast: str
    previous: str


def _parse_event_time(
    date_str: str, time_str: str
) -> tuple[datetime | None, str]:
    """Parse Forex Factory's UTC date+time into (ET datetime, display label).

    Returns (None, "") if the date itself is unparseable.
    """
    time_str = (time_str or "").strip()

    try:
        base = datetime.strptime(date_str, "%m-%d-%Y").replace(tzinfo=UTC)
    except ValueError:
        return None, time_str or ""

    if not time_str or time_str.lower() == "all day":
        when = base.replace(hour=12).astimezone(ET_TZ)
        return when, "終日"

    if time_str.lower() == "tentative":
        when = base.replace(hour=23, minute=59).astimezone(ET_TZ)
        return when, "未定"

    try:
        dt_utc = datetime.strptime(
            f"{date_str} {time_str.upper()}", "%m-%d-%Y %I:%M%p"
        ).replace(tzinfo=UTC)
        dt_et = dt_utc.astimezone(ET_TZ)
        return dt_et, dt_et.strftime("%H:%M")
    except ValueError:
        return None, time_str


def fetch_events(timeout: float = 30.0) -> list[CalendarEvent]:
    """Fetch the current week's events from Forex Factory.

    Raises urllib.error.URLError on network failure.
    """
    req = urllib.request.Request(FF_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()

    root = ET.fromstring(raw)
    events: list[CalendarEvent] = []
    for ev in root.findall("event"):
        title = (ev.findtext("title") or "").strip()
        country = (ev.findtext("country") or "").strip()
        impact = (ev.findtext("impact") or "").strip()
        date_str = (ev.findtext("date") or "").strip()
        time_str = (ev.findtext("time") or "").strip()
        forecast = (ev.findtext("forecast") or "").strip()
        previous = (ev.findtext("previous") or "").strip()

        when_et, label = _parse_event_time(date_str, time_str)
        events.append(
            CalendarEvent(
                when_et=when_et,
                time_label=label,
                country=country,
                impact=impact,
                title=title,
                forecast=forecast,
                previous=previous,
            )
        )
    return events


def next_business_day(now_et: datetime) -> date:
    """The next weekday strictly after now_et's ET date."""
    d = now_et.date() + timedelta(days=1)
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d += timedelta(days=1)
    return d


def filter_events(
    events: list[CalendarEvent],
    target_date: date,
    currencies: list[str],
    impacts: list[str],
) -> list[CalendarEvent]:
    cur_set = {c.upper() for c in currencies}
    imp_set = {i for i in impacts}

    matched = [
        e
        for e in events
        if e.when_et is not None
        and e.when_et.date() == target_date
        and e.country.upper() in cur_set
        and e.impact in imp_set
    ]
    matched.sort(key=lambda e: e.when_et)
    return matched
