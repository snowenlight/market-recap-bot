from __future__ import annotations

import smtplib
from email.message import EmailMessage


def send_email(
    *,
    sender: str,
    app_password: str,
    recipient: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> None:
    # Gmail shows app passwords as "abcd efgh ijkl mnop"; copy-paste can
    # include NBSPs that smtplib chokes on. Strip all whitespace.
    app_password = "".join(app_password.split())

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(msg)
