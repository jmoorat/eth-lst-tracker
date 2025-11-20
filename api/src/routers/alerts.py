from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas.alert
from data_access import alerts as alert_data
from database import get_db
from schemas.auth import AuthenticatedUser
from security import get_current_user
from utils.email import is_email_address_in_whitelist

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post(
    "",
    response_model=schemas.alert.Alert,
    status_code=201,
)
def create_alert(
    alert: schemas.alert.AlertCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.alert.Alert:
    """Create a new alert after validating ownership, whitelist, and market availability."""
    user_email = current_user.email

    if alert.email != user_email:
        raise HTTPException(status_code=403, detail="Authenticated user does not match alert email.")

    if not is_email_address_in_whitelist(alert.email):
        raise HTTPException(
            status_code=401,
            detail="Email address not allowed",
        )

    if alert.is_primary_market and alert.network != "ethereum":
        raise HTTPException(status_code=400, detail="Primary market is only available on Ethereum")

    if not alert_data.check_available_token_network_market_type(
        db, alert.token_name, alert.network, alert.is_primary_market
    ):
        raise HTTPException(
            status_code=400,
            detail="The specified token, network, and market type combination is not available.",
        )

    alert_created: schemas.alert.Alert = alert_data.create_alert(db, alert)
    return alert_created
