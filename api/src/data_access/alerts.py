from sqlalchemy.orm import Session

import models
import schemas.alert


def check_available_token_network_market_type(
    db: Session, token_name: str, network: str, is_primary_market: bool
) -> bool:
    result = (
        db.query(models.TokenListing)
        .filter(
            models.TokenListing.token_name == token_name,
            models.TokenListing.network == network,
            models.TokenListing.is_primary_market == is_primary_market,
        )
        .first()
    )
    return result is not None


def create_alert(db: Session, alert: schemas.alert.AlertCreate):
    """Create an Alert row from a Pydantic AlertCreate."""
    data = alert.model_dump()
    alert_model = models.Alert(**data)
    db.add(alert_model)
    db.commit()
    db.refresh(alert_model)
    return schemas.alert.Alert.model_validate(alert_model, from_attributes=True)


def get_active_alerts(db: Session):
    """Get all active alerts that need to be evaluated."""
    return db.query(models.Alert).filter(models.Alert.status == schemas.alert.AlertStatus.ACTIVE).all()


def save_alert(db: Session, alert: models.Alert):
    """Persist changes to an existing alert."""
    db.commit()
    db.refresh(alert)
    return alert
