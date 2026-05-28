from __future__ import annotations

import html
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
        if _is_html(summary):
            lines.append("(HTML版メールを参照してください)")
        else:
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


def _is_html(text: str) -> bool:
    head = text.lstrip()[:200].lower()
    return head.startswith("<!doctype") or head.startswith("<html")


def _build_market_block_html(
    groups: list[Group],
    quotes_by_symbol: dict[str, Quote | None],
    calendar_lines: list[str] | None,
) -> str:
    lines: list[str] = []
    for group in groups:
        lines.append(f"■ {group.name}")
        for inst in group.instruments:
            q = quotes_by_symbol.get(inst.symbol)
            lines.append(_fmt_quote(q) if q is not None else _fmt_missing(inst.label))
        lines.append("")
    if calendar_lines:
        lines.extend(calendar_lines)
    return html.escape("\n".join(lines).rstrip())


def _market_section_html(
    groups: list[Group],
    quotes_by_symbol: dict[str, Quote | None],
    calendar_lines: list[str] | None,
    sources: list[str],
) -> str:
    market_pre = _build_market_block_html(groups, quotes_by_symbol, calendar_lines)
    sources_line = html.escape(f"データソース: {', '.join(sources)}")
    return (
        '\n      <tr><td style="border-top:1px solid #dddddd;"></td></tr>\n'
        '      <tr><td style="padding:20px 24px;">\n'
        '        <h2 style="font-size:16px; color:#1a3a5c; margin:0 0 12px 0;">7. マーケット数値 (Yahoo Finance / Forex Factory)</h2>\n'
        f'        <pre style="font-family:\'Courier New\',Courier,monospace; font-size:13px; margin:0; white-space:pre; color:#333333;">{market_pre}</pre>\n'
        f'        <p style="margin:12px 0 0 0; font-size:12px; color:#888888;">{sources_line}<br>本メールは個人プロジェクトの自動配信です。投資助言ではありません。</p>\n'
        '      </td></tr>\n'
    )


def build_html_body(
    groups: list[Group],
    quotes_by_symbol: dict[str, Quote | None],
    calendar_lines: list[str] | None = None,
    summary: str | None = None,
    *,
    sources: list[str] | None = None,
    now: datetime | None = None,
) -> str | None:
    """Return an HTML body for the email, or None when no HTML rendering is needed."""
    sources = sources or ["Yahoo Finance"]
    now = now or datetime.now(JST)

    market_html = _market_section_html(groups, quotes_by_symbol, calendar_lines, sources)

    if summary and _is_html(summary):
        # Gemini returns a complete HTML document; inject our market section
        # just before </body> so the styled template stays intact.
        marker = "</body>"
        idx = summary.lower().rfind(marker)
        if idx != -1:
            return summary[:idx] + market_html + summary[idx:]
        return summary + market_html

    # Fallback: build a minimal HTML wrapper.
    title = html.escape(f"Market Recap {now:%Y/%m/%d}")
    summary_block = (
        f'<pre style="font-family:\'Courier New\',Courier,monospace; font-size:13px; white-space:pre;">{html.escape(summary)}</pre>'
        if summary
        else ""
    )
    return (
        '<!DOCTYPE html>\n'
        '<html lang="ja"><head><meta charset="UTF-8"><title>'
        f'{title}</title></head>\n'
        '<body style="font-family:Arial,\'Helvetica Neue\',Helvetica,sans-serif; line-height:1.6; color:#333333;">\n'
        '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;">\n'
        f'{summary_block}\n{market_html}\n'
        '</table>\n'
        '</body></html>\n'
    )
