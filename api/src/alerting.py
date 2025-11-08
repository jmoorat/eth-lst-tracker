"""Alert evaluation entry points used by background workers."""

from __future__ import annotations

import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from sqlalchemy.orm import Session

import crud
from models import Alert, LstPrice
from schemas import AlertStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_ADDR = os.getenv("FROM_ADDR")

def send_mail_notification(to_address: str, subject: str, body: str) -> None:
    """Send an email notification.

    This is a stub implementation. Replace it with actual email sending logic.
    """

    msg = EmailMessage()
    msg["From"] = FROM_ADDR
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)


def evaluate_alert_condition(alert: Alert, current_price: dict) -> bool:
    """Evaluate if the alert condition is met based on the current price."""
    value_to_evaluate = current_price["price_eth"] if alert.metric == "price_eth" else current_price["premium_percentage"]

    if alert.comparison == "lt":
        return value_to_evaluate < alert.target_value
    elif alert.comparison == "lte":
        return value_to_evaluate <= alert.target_value
    elif alert.comparison == "gt":
        return value_to_evaluate > alert.target_value
    elif alert.comparison == "gte":
        return value_to_evaluate >= alert.target_value
    elif alert.comparison == "eq":
        return value_to_evaluate == alert.target_value
    else:
        logger.error(f"Unknown alert condition: {alert.comparison}")
        return False


def run_alert_checks(db: Session) -> None:
    """Evaluate active alerts and trigger notifications.

    The concrete implementation depends on how alerts are stored and how
    notifications should be delivered. The APScheduler background job configured
    in ``api/src/main.py`` will call this function every 10 minutes.
    """

    # Get all active alerts and current prices
    alerts: list[Alert] = crud.get_alerts_to_evaluate(db)
    current_prices: list[dict] = crud.get_last_prices(db)

    for alert in alerts:
        current_price = next(
            (
                price
                for price in current_prices
                if price["token_name"] == alert.token_name
                and price["network"] == alert.network
                and price["is_primary_market"] == alert.is_primary_market
            ),
            None,
        )
        if not current_price:
            logger.warning(
                f"No current price found for alert {alert.id} "
                f"({alert.token_name} on {alert.network}, primary market: {alert.is_primary_market})"
            )
            continue

        is_triggered = evaluate_alert_condition(alert, current_price)

        if not is_triggered:
            continue

        # Send notification
        subject = f"Alert triggered for the {"price" if alert.metric == "price_eth" else "premium"} of {alert.token_name} on {alert.network}"
        body = (
            f"Your alert for {alert.token_name} on {alert.network} has been triggered.\n\n"
            f"Current {alert.metric}: "
            f"{current_price["price_eth"] if alert.metric == 'price_eth' else current_price["premium_percentage"]}\n"
            f"Target value: {alert.target_value}\n"
            f"Comparison: {alert.comparison}\n\n"
            f"Alert ID: {str(alert.id).split("-")[0]}\n\n"
            "This is an automated message."
        )
        try:
            send_mail_notification(alert.email, subject, body)
            logger.info(f"Sent alert notification for alert {alert.id}")
        except Exception as e:
            logger.error(f"Failed to send alert notification to {alert.email}: {str(e)}")
            continue

        # Update alert status
        alert.trigger_count += 1
        alert.last_triggered_at = datetime.utcnow()
        alert.status = AlertStatus.TRIGGERED
        crud.save_alert(db, alert)