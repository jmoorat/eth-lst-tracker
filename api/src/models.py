from sqlalchemy import Boolean, Column, DateTime, Numeric, String, Enum, Integer, func, ForeignKey, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from database import Base


class LstPrice(Base):
    """
    Represents a price of a token on a network at a given time in the database
    """

    __tablename__ = "prices"

    timestamp = Column(DateTime(timezone=True), primary_key=True)
    token_name = Column(String(10), primary_key=True)
    network = Column(String(20), primary_key=True)
    is_primary_market = Column(Boolean, primary_key=True)
    price_eth = Column(Numeric(20, 18))
    price_usd = Column(Numeric(16, 2))
    premium = Column(Numeric(6, 5))

class TokenListing(Base):
    """
    Represents a token listing on a given network in the database
    """

    __tablename__ = "token_listings"

    token_name = Column(String(10), primary_key=True)
    network = Column(String(20), primary_key=True)
    is_primary_market = Column(Boolean, primary_key=True)


class Alert(Base):
    """
    Alert for a token price or premium on a given network and market type
    """

    __tablename__ = "alerts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email = Column(String(255), nullable=False)
    token_name = Column(String(10), nullable=False)
    network = Column(String(20), nullable=False)
    is_primary_market = Column(Boolean, nullable=False)
    metric = Column(Enum("price_eth", "premium", name="alert_metric"), nullable=False)  # 'price_eth' or 'premium_percentage'
    threshold = Column(Numeric(20, 10), nullable=False)
    condition = Column(
        Enum("lt", "lte", "gt", "gte", "eq", name="alert_condition"), nullable=False
    )
    status = Column(
        Enum("active", "triggered", "paused", "cancelled", name="alert_status"),
        nullable=False,
        default="active",
    )
    type = Column(Enum("one_off", "recurrent", name="alert_type"), nullable=False)
    note = Column(String(500))
    trigger_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_triggered_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    __table_args__ = (
        ForeignKeyConstraint(
            ["token_name", "network", "is_primary_market"],
            ["token_listings.token_name", "token_listings.network", "token_listings.is_primary_market"],
            ondelete="CASCADE",
        ),
    )
