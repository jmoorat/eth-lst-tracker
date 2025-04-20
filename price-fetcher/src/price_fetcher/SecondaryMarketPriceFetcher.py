from abc import ABC, abstractmethod


class UnsupportedChainException(Exception):
    pass


class UnsupportedTokenException(Exception):
    pass


class CannotGetPriceException(Exception):
    pass


class SecondaryMarketPriceFetcher(ABC):
    one_ether = 10**18

    @abstractmethod
    def get_price(
        self, network: str, token_address: str, eth_token_address: str
    ) -> int:
        """
        Get price in ETH from secondary market for given token on given network

        Args:
            chain_id (int): chain id
            token_address (str): token address on network with given chain id
            eth_token_address (str): ETH token address on network with given chain id

        Returns:
            int: price in wei

        Raises:
            UnsupportedChainException: if chain id is not supported
            UnsupportedTokenException: if token is not supported
            CannotGetPriceException: if price cannot be fetched
        """
        pass
