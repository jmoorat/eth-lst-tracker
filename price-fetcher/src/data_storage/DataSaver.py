from datetime import datetime
from decimal import Decimal
from abc import ABC, abstractmethod
from typing import Optional


class FailedToSaveDataPointException(Exception):
    pass


class DataSaver(ABC):

    @abstractmethod
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
        """
        Save data point to database

        Args:
            timestamp (datetime): data point datetime
            token_name (str): token name
            price_eth (int | Decimal): price in ETH
            price_usd (float): price in USD
            network (str): network / chain name
            is_primary_market (bool): whether price is from primary market
            premium (float): premium

        Raises:
            FailedToSaveDataPointException: if data point cannot be saved
        """
        pass
