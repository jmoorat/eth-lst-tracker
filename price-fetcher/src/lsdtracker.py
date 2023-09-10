import datetime
import json
import logging
import os
from argparse import ArgumentParser
import sys
import time
import schedule
from web3 import Web3

from data_storage.DataSaver import DataSaver
from data_storage.FakeDataSaver import FakeDataSaver
from data_storage.PostgresDataSaver import PostgresDataSaver
from price_fetcher.OneInchPriceFetcher import OneInchPriceFetcher
from price_fetcher.SecondaryMarketPriceFetcher import SecondaryMarketPriceFetcher
from utils import eth_price_to_string, get_premium, chains

DATABASE_URL = os.getenv("DATABASE_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HTTP_PROXY = os.getenv("HTTP_PROXY")
ONE_INCH_API_KEY = os.getenv("ONE_INCH_API_KEY")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
LONG_RUN = os.getenv("LONG_RUN", "false").lower() == "true"
SCHEDULE_MINUTES = int(os.getenv("SCHEDULE_MINUTES", "5"))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
)


def load_config(config_file_path: str):
    """
    Loads config
    """
    with open(config_file_path) as f:
        return json.load(f)


def main(
        config: dict,
        web3_provider: Web3,
        price_fetcher: SecondaryMarketPriceFetcher,
        data_saver: DataSaver
):
    primary_market_price = 0
    now = datetime.datetime.now()

    for token in config["lsd_tokens"]:

        # Get primary market price
        if (
            "ethereum" in token["token_addresses"]
            and "native_contract_abi" in token
            and "get_exchange_rate_function_name" in token
        ):
            token_address = token["token_addresses"]["ethereum"]
            chain = "ethereum"
            contract = web3_provider.eth.contract(
                address=token_address, abi=token["native_contract_abi"]
            )
            get_exchange_rate_function = contract.functions[
                token["get_exchange_rate_function_name"]
            ]
            primary_market_price = get_exchange_rate_function().call()
            if primary_market_price >= 0:
                logging.info(
                    f"Primary market price for {token['token_name']} on {chain} is "
                    f"{eth_price_to_string(primary_market_price)} ETH"
                )
                data_saver.save_data_point(
                    timestamp=now,
                    token_name=token["token_name"],
                    price_eth=web3_provider.from_wei(primary_market_price, "ether"),
                    price_usd=None,
                    network=chain,
                    is_primary_market=True,
                    premium=0,
                )

        # Get secondary market prices on given chains
        for chain in token["token_addresses"]:
            token_address = token["token_addresses"][chain]
            price = price_fetcher.get_price(
                chains[chain]["chain_id"],
                token_address,
                chains[chain]["eth_token_address"],
            )
            premium = get_premium(primary_market_price, price)

            if price >= 0:
                logging.info(
                    f"{token['token_name']} on {chain} is {eth_price_to_string(price)} ETH -> "
                    f"{abs(premium * 100):.3f}% {'premium' if premium >= 0 else 'discount'}"
                )
                data_saver.save_data_point(
                    timestamp=now,
                    token_name=token["token_name"],
                    price_eth=web3_provider.from_wei(price, "ether"),
                    price_usd=None,
                    network=chain,
                    is_primary_market=False,
                    premium=premium
                )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", help="config file path")
    args = parser.parse_args()
    if not args.config:
        parser.error("A config file is required")

    loaded_config = load_config(args.config)
    w3 = Web3(Web3.HTTPProvider(os.environ.get("WEB3_PROVIDER")))
    secondary_market_price_fetcher: SecondaryMarketPriceFetcher = OneInchPriceFetcher(
        ONE_INCH_API_KEY, HTTP_PROXY
    )
    if DRY_RUN:
        data_saver: DataSaver = FakeDataSaver()
    else:
        data_saver: DataSaver = PostgresDataSaver(DATABASE_URL)

    if not LONG_RUN:
        main(loaded_config, w3, secondary_market_price_fetcher, data_saver)
    else:
        schedule.every(SCHEDULE_MINUTES).minutes.do(main, loaded_config, w3, secondary_market_price_fetcher, data_saver)
        logging.info(f"Running every {SCHEDULE_MINUTES} minutes")
        while (LONG_RUN):
            schedule.run_pending()
            time.sleep(1)
