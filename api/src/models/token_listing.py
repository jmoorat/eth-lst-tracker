from sqlalchemy import Boolean, Column, String

from database import Base


class TokenListing(Base):
    """Represents an available token/network pairing."""

    __tablename__ = "token_listings"

    token_name = Column(String(10), primary_key=True)
    network = Column(String(20), primary_key=True)
    is_primary_market = Column(Boolean, primary_key=True)
