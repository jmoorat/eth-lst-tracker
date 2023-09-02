import requests
import time

from ports.SecondaryMarketPriceFetcher import SecondaryMarketPriceFetcher, UnsupportedChainException


class ParaswapPriceFetcher(SecondaryMarketPriceFetcher):
    def __init__(self, http_proxy: str):
        self.http_proxies = {
            "http": http_proxy,
            "https": http_proxy,
        }
        self.supported_chain_ids = [
            1, # ethereum
            42161, # arbitrum
            10, # optimism
            137, # polygon
            43114, # avalanche
            56, # bsc
            250, # fantom
        ]

    def get_price(self, chain_id: int, token_address: str, eth_token_address: str) -> int:
        if chain_id not in self.supported_chain_ids:
            raise UnsupportedChainException(f"Chain id {chain_id} is not supported by Paraswap")

        time.sleep(1)  # rate limit
        quote_params = {
            "srcToken": token_address,
            "destToken": eth_token_address,
            "amount": str(SecondaryMarketPriceFetcher.one_ether),
            "srcDecimals": "18",
            "destDecimals": "18",
            "side": "SELL",
            "network": chain_id,
        }
        url = f"https://apiv5.paraswap.io/prices/?{requests.compat.urlencode(quote_params)}"

        try:
            response = requests.get(
                url, proxies=self.http_proxies
            )
        except Exception as e:
            raise CannotGetPriceException(f"Failed to get secondary market rate for {token_address} on chain {chain_id} with Paraswap: {str(e)}")

        if response.status_code != 200:
            raise CannotGetPriceException(f"{response.status_code} error from Paraswap: {response.reason}")

        data = response.json()
        return int(data["priceRoute"]["destAmount"])