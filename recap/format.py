from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

from recap.calendar import CalendarEvent
from recap.config import Group
from recap.data import Quote

JST = timezone(timedelta(hours=9))
WEEKDAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]

LABEL_WIDTH = 10


def _fmt_quote(q: Quote) -> str:
    kind = q.instrument.kind
    label = f"{q.instrument.label:<{LABEL_WIDTH}}"

    if kind == "yield":
        # Yahoo returns yields as percent values (e.g. 4.32 = 4.32%).
        change_bp = (q.last - q.prev) * 100.0
        return f"  {label} {q.last:>7.2f}%   ({change_bp:+.1f}bp)"

    if kind == "fx_jpy":
        return f"  {label} {q.last:>10.2f}   ({q.change_pct:+.2f}%)"

    if kind == "fx":
        return f"  {label} {q.last:>10.4f}   ({q.change_pct:+.2f}%)"

    # index (default)
    return f"  {label} {q.last:>12,.2f}   ({q.change_pct:+.2f}%)"


def _fmt_missing(label: str) -> str:
    return f"  {label:<{LABEL_WIDTH}}  (取得失敗)"


def build_subject(now: datetime | None = None) -> str:
    now = now or datetime.now(JST)
    return f"【Market Recap】{now:%Y/%m/%d} ({WEEKDAYS_JA[now.weekday()]}) NY引け"


def _fmt_event(e: CalendarEvent) -> str:
    parts: list[str] = []
    if e.forecast:
        parts.append(f"予想 {e.forecast}")
    if e.previous:
        parts.append(f"前回 {e.previous}")
    suffix = f" ({' / '.join(parts)})" if parts else ""

    time_part = e.time_label
    if time_part not in ("終日", "未定"):
        time_part = f"{time_part} ET"

    return f"  {time_part}  {e.title}{suffix}"


def build_calendar_section(
    target_date: date,
    events: list[CalendarEvent],
    *,
    fetch_failed: bool = False,
) -> list[str]:
    weekday = WEEKDAYS_JA[target_date.weekday()]
    md = f"{target_date.month}/{target_date.day}"
    header = f"■ 翌営業日 ({md}{weekday}) の注目指標"

    if fetch_failed:
        return [header, "  (取得失敗)", ""]
    if not events:
        return [header, "  予定なし", ""]
    return [header, *(_fmt_event(e) for e in events), ""]


def build_body(
    groups: list[Group],
    quotes_by_symbol: dict[str, Quote | None],
    calendar_lines: list[str] | None = None,
    summary: str | None = None,
    *,
    sources: list[str] | None = None,
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(JST)
    sources = sources or ["Yahoo Finance"]

    lines: list[str] = [
        f"【Market Recap】 {now:%Y/%m/%d} ({WEEKDAYS_JA[now.weekday()]}) NY引け",
        "",
    ]

    if summary:
        lines.append("■ 本日のサマリー")
        lines.append(summary)
        lines.append("")

    for group in groups:
        lines.append(f"■ {group.name}")
        for inst in group.instruments:
            q = quotes_by_symbol.get(inst.symbol)
            if q is None:
                lines.append(_fmt_missing(inst.label))
            else:
                lines.append(_fmt_quote(q))
        lines.append("")

    if calendar_lines:
        lines.extend(calendar_lines)

    lines.extend([
        f"データソース: {', '.join(sources)}",
        "本メールは個人プロジェクトの自動配信です。投資助言ではありません。",
    ])
    return "\n".join(lines)
