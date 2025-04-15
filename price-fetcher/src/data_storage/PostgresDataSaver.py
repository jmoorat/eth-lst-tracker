from typing import Optional
from _decimal import Decimal
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Numeric, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from data_storage.DataSaver import DataSaver, FailedToSaveDataPointException

Base = declarative_base()


class LstPriceDataPoint(Base):
    """
    Represents a price of a token on a network at a given time in the database
    """

    __tablename__ = "prices"

    timestamp = Column(DateTime(timezone=True), primary_key=True)
    token_name = Column(String(10), primary_key=True)
    network = Column(String(20), primary_key=True)
    price_eth = Column(Numeric(20, 18))
    price_usd = Column(Numeric(16, 2))
    is_primary_market = Column(Boolean)
    premium = Column(Numeric(6, 5))


class PostgresDataSaver(DataSaver):
    def __init__(self, db_connection_string: str):
        self.engine = create_engine(db_connection_string)
        self.session_maker = sessionmaker(bind=self.engine)

    def save_data_point(
            self,
            timestamp: datetime,
            token_name: str,
            price_eth: int | Decimal,
            price_usd: Optional[float],
            network: str,
            is_primary_market: bool,
            premium: float
    ):
        session = self.session_maker()
        try:
            lst_price_data_point = LstPriceDataPoint(
                timestamp=timestamp,
                token_name=token_name,
                price_eth=price_eth,
                price_usd=price_usd,
                network=network,
                is_primary_market=is_primary_market,
                premium=premium
            )
            session.add(lst_price_data_point)
            session.commit()
        except Exception as e:
            session.rollback()
            raise FailedToSaveDataPointException(f"Failed to save data point: {str(e)}")
        finally:
            session.close()
