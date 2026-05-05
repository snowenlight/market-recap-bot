from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from recap.config import load_groups
from recap.data import fetch_quote
from recap.format import build_body, build_subject
from recap.mail import send_email

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "instruments.yaml"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"missing required env var: {name}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to instruments YAML",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the email to stdout instead of sending",
    )
    args = parser.parse_args()

    load_dotenv()

    groups = load_groups(args.config)

    quotes_by_symbol = {}
    for group in groups:
        for inst in group.instruments:
            quotes_by_symbol[inst.symbol] = fetch_quote(inst)

    subject = build_subject()
    body = build_body(groups, quotes_by_symbol)

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
