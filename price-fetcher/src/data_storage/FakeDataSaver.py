import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from data_storage.DataSaver import DataSaver


class FakeDataSaver(DataSaver):

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
        logging.debug(f"Saving data point: {timestamp}, {token_name}, {price_eth}, {price_usd}, {network}, {is_primary_market}, {premium}")
        return
