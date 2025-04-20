from web3 import Web3

chains = {
    "ethereum": {
        "chain_id": 1,
        "eth_token_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    },
    "arbitrum": {
        "chain_id": 42161,
        "eth_token_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    },
    "optimism": {
        "chain_id": 10,
        "eth_token_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    },
    "polygon": {
        "chain_id": 137,
        "eth_token_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    },
    "gnosis": {
        "chain_id": 100,
        "eth_token_address": "0x6a023ccd1ff6f2045c3309768ead9e68f978f6e1",
    },
    "base": {
        "chain_id": 8453,
        "eth_token_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    },
    "zksync": {
        "chain_id": 324,
        "eth_token_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    },
}


def eth_price_to_string(eth_amount: int) -> str:
    """
    Converts an ETH amount in wei to a string

    Args:
        eth_amount (int): The amount of ETH in wei

    Returns:
        str: The amount of ETH in ether
    """
    rem: int = eth_amount % 10**12
    return Web3.from_wei(eth_amount - rem, "ether")


def get_premium(primary_market_price, secondary_market_price) -> float:
    """
    Returns the premium given a primary market price (benchmark price, Net asset value) and a secondary market price

    Args:
        primary_market_price (int): The primary market price (benchmark price)
        secondary_market_price (int): The secondary market price
    """
    return (secondary_market_price - primary_market_price) / primary_market_price
