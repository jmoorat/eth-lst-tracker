import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_ADDR = os.getenv("FROM_ADDR", "")


def normalize_email(email: str) -> str:
    """Normalize email addresses for comparisons and storage."""

    return email.strip().lower()


def is_email_address_in_whitelist(email: str) -> bool:
    """Check if the given email address is in the allowed whitelist."""

    whitelist_env = os.getenv("EMAIL_RECIPIENT_WHITELIST", "")
    if whitelist_env.strip() in ("", "*"):
        return True
    whitelist = {normalize_email(address) for address in whitelist_env.split(",") if address.strip()}
    return normalize_email(email) in whitelist


def send_mail_notification(to_address: str, subject: str, body: str) -> None:
    """Send an email notification using the configured SMTP relay."""

    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and FROM_ADDR):
        raise RuntimeError("SMTP configuration is incomplete. Check SMTP_* and FROM_ADDR env vars.")

    msg = EmailMessage()
    msg["From"] = FROM_ADDR
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    logger.info("Sending email to %s via %s:%s", to_address, SMTP_HOST, SMTP_PORT)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
