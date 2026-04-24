from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from fastapi import HTTPException
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


@dataclass
class DeliveryResult:
    channel: str
    provider: str
    status: str
    external_id: str | None = None
    detail: str | None = None


def _twilio_client() -> tuple[Client, str]:
    try:
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        from_number = os.environ["TWILIO_PHONE_NUMBER"]
    except KeyError as exc:
        missing = str(exc).strip("'")
        raise HTTPException(status_code=400, detail=f"Missing Twilio configuration: {missing}")
    return Client(account_sid, auth_token), from_number


def _send_sms(message: str, recipient: str) -> DeliveryResult:
    client, from_number = _twilio_client()
    try:
        msg = client.messages.create(body=message, from_=from_number, to=recipient)
    except TwilioRestException as exc:
        raise HTTPException(status_code=502, detail=f"Twilio SMS failed: {exc.msg}") from exc
    return DeliveryResult(
        channel="sms",
        provider="twilio",
        status="sent",
        external_id=msg.sid,
    )


def _send_whatsapp(message: str, recipient: str) -> DeliveryResult:
    client, from_number = _twilio_client()
    # Use WhatsApp sandbox number if configured, else fall back to regular number
    wa_from = os.environ.get("TWILIO_WHATSAPP_FROM", from_number)
    if not wa_from.startswith("whatsapp:"):
        wa_from = f"whatsapp:{wa_from}"
    wa_to = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"
    try:
        msg = client.messages.create(body=message, from_=wa_from, to=wa_to)
    except TwilioRestException as exc:
        raise HTTPException(status_code=502, detail=f"Twilio WhatsApp failed: {exc.msg}") from exc
    return DeliveryResult(
        channel="whatsapp",
        provider="twilio",
        status="sent",
        external_id=msg.sid,
    )


def _send_email(message: str, recipient: str, subject: str | None = None) -> DeliveryResult:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("SMTP_FROM_EMAIL")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"

    if not host or not from_email:
        raise HTTPException(status_code=400, detail="Missing SMTP configuration: SMTP_HOST/SMTP_FROM_EMAIL")

    email = EmailMessage()
    email["From"] = from_email
    email["To"] = recipient
    email["Subject"] = subject or "SAARTHI Follow-up Summary"
    email.set_content(message)

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(email)
    except OSError as exc:
        raise HTTPException(status_code=502, detail=f"SMTP delivery failed: {exc}") from exc

    return DeliveryResult(channel="email", provider="smtp", status="sent")


def deliver_message(channel: str, message: str, recipient: str, subject: str | None = None) -> DeliveryResult:
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient is required")
    if channel == "sms":
        return _send_sms(message, recipient)
    if channel == "whatsapp":
        return _send_whatsapp(message, recipient)
    if channel == "email":
        return _send_email(message, recipient, subject=subject)
    raise HTTPException(status_code=400, detail=f"Unsupported channel: {channel}")
