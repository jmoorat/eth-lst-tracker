from .database import Base
from sqlalchemy import Column, Numeric, String, Boolean, DateTime


class LsdPrice(Base):
    """
    Represents a price of a token on a network at a given time in the database
    """
    __tablename__ = 'prices'

    timestamp = Column(DateTime(timezone=True), primary_key=True)
    token_name = Column(String(10), primary_key=True)
    network = Column(String(20), primary_key=True)
    price_eth = Column(Numeric(20, 18))
    price_usd = Column(Numeric(16, 2))
    is_primary_market = Column(Boolean, primary_key=True)
    premium = Column(Numeric(6, 5))