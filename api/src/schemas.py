from pydantic import BaseModel

class LsdPrice(BaseModel):
    timestamp: str
    token_name: str
    network: str
    price_eth: float
    price_usd: float
    is_primary_market: bool
    premium: float

    # transform premium to percentage
    @property
    def premium_percentage(self):
        return self.premium * 100