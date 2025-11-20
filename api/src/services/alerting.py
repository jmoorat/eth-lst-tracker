"""Alert evaluation entry points used by background workers."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from data_access import alerts as alert_data
from data_access import prices as price_data
from models import Alert
from schemas.alert import AlertStatus
from utils.email import send_mail_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def evaluate_alert_condition(alert: Alert, current_price: dict) -> bool:
    """Evaluate if the alert condition is met based on the current price."""
    value_to_evaluate = (
        current_price["price_eth"] if alert.metric == "price_eth" else current_price["premium_percentage"]
    )

    if alert.condition == "lt":
        return value_to_evaluate < alert.threshold
    elif alert.condition == "lte":
        return value_to_evaluate <= alert.threshold
    elif alert.condition == "gt":
        return value_to_evaluate > alert.threshold
    elif alert.condition == "gte":
        return value_to_evaluate >= alert.threshold
    elif alert.condition == "eq":
        return value_to_evaluate == alert.threshold
    else:
        logger.error("Unknown alert condition: %s", alert.condition)
        return False


def run_alert_checks(db: Session) -> None:
    """Evaluate active alerts and trigger notifications."""
    alerts: list[Alert] = alert_data.get_active_alerts(db)
    current_prices: list[dict] = price_data.get_last_prices(db)

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
                "No current price found for alert %s (%s on %s, primary market: %s)",
                alert.id,
                alert.token_name,
                alert.network,
                alert.is_primary_market,
            )
            continue

        is_triggered = evaluate_alert_condition(alert, current_price)

        if not is_triggered:
            continue

        alert_metric_name = "price" if alert.metric == "price_eth" else "premium"
        subject = f"Alert triggered for the {alert_metric_name} of {alert.token_name} on {alert.network}"
        body = (
            f"Your alert for {alert.token_name} on {alert.network} has been triggered.\n\n"
            f"Current {alert.metric}: "
            f"{current_price['price_eth'] if alert.metric == 'price_eth' else current_price['premium_percentage']}\n"
            f"Threshold: {alert.threshold}\n"
            f"Condition: {alert.condition}\n\n"
            f"Alert ID: {str(alert.id).split('-')[0]}\n\n"
            "This is an automated message."
        )
        try:
            send_mail_notification(alert.email, subject, body)
            logger.info("Sent alert notification for alert %s", alert.id)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("Failed to send alert notification to %s: %s", alert.email, exc)
            continue

        alert.trigger_count += 1
        alert.last_triggered_at = datetime.utcnow()
        alert.status = AlertStatus.TRIGGERED
        alert_data.save_alert(db, alert)
