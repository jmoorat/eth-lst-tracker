import time

import requests

from price_fetcher.SecondaryMarketPriceFetcher import (
    CannotGetPriceException,
    SecondaryMarketPriceFetcher,
    UnsupportedChainException,
)


class OneInchPriceFetcher(SecondaryMarketPriceFetcher):
    def __init__(self, one_inch_api_key: str, http_proxy: str):
        self.one_inch_api_key = one_inch_api_key
        self.http_proxies = {
            "http": http_proxy,
            "https": http_proxy,
        }
        self.supported_chain_ids = [
            1, # ethereum
            42161, # arbitrum
            10, # optimism
            137, # polygon
            100, # gnosis
            8453, # base
            324, # zksync
        ]

    def get_price(self, chain_id: int, token_address: str, eth_token_address: str) -> int:
        if chain_id not in self.supported_chain_ids:
            raise UnsupportedChainException(f"Chain id {chain_id} is not supported by 1inch")

        time.sleep(1)  # rate limit
        quote_params = {
            "src": token_address,
            "dst": eth_token_address,
            "amount": str(SecondaryMarketPriceFetcher.one_ether),
        }
        url = f"https://api.1inch.dev/swap/v5.2/{chain_id}/quote?{requests.compat.urlencode(quote_params)}"

        try:
            response = requests.get(
                url, proxies=self.http_proxies, headers={"Authorization": self.one_inch_api_key}
            )
        except Exception as e:
            raise CannotGetPriceException(f"Failed to get secondary market rate for {token_address} on chain {chain_id} with 1inch: {str(e)}")

        if response.status_code != 200:
            raise CannotGetPriceException(f"{response.status_code} error from 1inch: {response.reason}")

        data = response.json()
        return int(data["toAmount"])
