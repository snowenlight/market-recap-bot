from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from recap.calendar import (
    ET_TZ,
    fetch_events,
    filter_events,
    next_business_day,
)
from recap.config import Config, load_config
from recap.data import fetch_quote
from recap.format import build_body, build_calendar_section, build_subject
from recap.llm import generate_summary, load_prompt
from recap.mail import send_email

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "instruments.yaml"
DEFAULT_PROMPT = ROOT / "config" / "prompt.md"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"missing required env var: {name}")
    return value


def _build_calendar_lines(config: Config) -> list[str]:
    cal_cfg = config.calendar
    if not cal_cfg.enabled:
        return []

    target = next_business_day(datetime.now(ET_TZ))
    try:
        events = fetch_events()
    except Exception as exc:
        print(f"calendar fetch failed: {exc}", file=sys.stderr)
        return build_calendar_section(target, [], fetch_failed=True)

    matched = filter_events(
        events, target, cal_cfg.currencies, cal_cfg.impacts
    )
    return build_calendar_section(target, matched)


def _build_summary(prompt_path: Path) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set; skipping summary", file=sys.stderr)
        return None
    try:
        prompt = load_prompt(prompt_path)
        return generate_summary(api_key=api_key, prompt=prompt)
    except Exception as exc:
        print(f"summary generation failed: {exc}", file=sys.stderr)
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to instruments YAML",
    )
    parser.add_argument(
        "--prompt",
        default=str(DEFAULT_PROMPT),
        help="Path to LLM prompt markdown",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the email to stdout instead of sending",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip the LLM summary step",
    )
    args = parser.parse_args()

    load_dotenv()

    config = load_config(args.config)

    quotes_by_symbol = {}
    for group in config.groups:
        for inst in group.instruments:
            quotes_by_symbol[inst.symbol] = fetch_quote(inst)

    calendar_lines = _build_calendar_lines(config)

    summary = None if args.no_summary else _build_summary(Path(args.prompt))

    sources = ["Yahoo Finance"]
    if config.calendar.enabled:
        sources.append("Forex Factory")
    if summary:
        sources.append("Gemini (Google Search)")

    subject = build_subject()
    body = build_body(
        config.groups,
        quotes_by_symbol,
        calendar_lines,
        summary,
        sources=sources,
    )

    if args.dry_run:
        print(f"Subject: {subject}\n")
        print(body)
        return

    sender = _require_env("GMAIL_ADDRESS")
    password = _require_env("GMAIL_APP_PASSWORD")
    recipient = _require_env("RECIPIENT")

    send_email(
        sender=sender,
        app_password=password,
        recipient=recipient,
        subject=subject,
        body=body,
    )
    print(f"sent to {recipient}")


if __name__ == "__main__":
    main()
