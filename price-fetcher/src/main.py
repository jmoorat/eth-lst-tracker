import datetime
import json
import logging
import os
from argparse import ArgumentParser
import sys
import time
import schedule
from web3 import Web3

from data_storage.DataSaver import DataSaver, FailedToSaveDataPointException
from data_storage.FakeDataSaver import FakeDataSaver
from data_storage.PostgresDataSaver import PostgresDataSaver
from price_fetcher.OneInchPriceFetcher import OneInchPriceFetcher
from price_fetcher.SecondaryMarketPriceFetcher import SecondaryMarketPriceFetcher, UnsupportedTokenException, \
    UnsupportedChainException, CannotGetPriceException
from utils import eth_price_to_string, get_premium, chains

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
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

    for token in config["tokens"]:

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
            try:
                primary_market_price = get_exchange_rate_function().call()
            except Exception as e:
                logging.warning(f"Failed to get primary market rate for {token['token_name']} on {chain}: {str(e)}")
                continue

            if primary_market_price >= 0:
                logging.info(
                    f"Primary market price for {token['token_name']} on {chain} is "
                    f"{eth_price_to_string(primary_market_price)} ETH"
                )
                try:
                    data_saver.save_data_point(
                        timestamp=now,
                        token_name=token["token_name"],
                        price_eth=web3_provider.from_wei(primary_market_price, "ether"),
                        price_usd=None,
                        network=chain,
                        is_primary_market=True,
                        premium=0,
                    )
                except FailedToSaveDataPointException as e:
                    logging.error(f"Failed to save data point: {str(e)}")

        # Get secondary market prices on given chains
        for chain in token["token_addresses"]:
            token_address = token["token_addresses"][chain]
            try:
                price = price_fetcher.get_price(
                    chains[chain]["chain_id"],
                    token_address,
                    chains[chain]["eth_token_address"],
                )
            except (UnsupportedChainException, UnsupportedTokenException, CannotGetPriceException) as e:
                logging.warning(f"Failed to get price for {token['token_name']} on {chain}: {str(e)}")
                continue

            premium = get_premium(primary_market_price, price)

            if price >= 0:
                logging.info(
                    f"{token['token_name']} on {chain} is {eth_price_to_string(price)} ETH -> "
                    f"{abs(premium * 100):.3f}% {'premium' if premium >= 0 else 'discount'}"
                )
                try:
                    data_saver.save_data_point(
                        timestamp=now,
                        token_name=token["token_name"],
                        price_eth=web3_provider.from_wei(price, "ether"),
                        price_usd=None,
                        network=chain,
                        is_primary_market=False,
                        premium=premium
                    )
                except FailedToSaveDataPointException as e:
                    logging.error(f"Failed to save data point: {str(e)}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", help="config file path")
    parser.add_argument("-d", "--dry-run", help="dry run", action="store_true")
    parser.add_argument("-l", "--long-run", help="long run", action="store_true",default=False if os.getenv("LONG_RUN") == None else os.getenv("LONG_RUN") == "true")
    parser.add_argument("-s", "--schedule", help="Number of minutes to wait between each run", default=5, type=int)
    args = parser.parse_args()
    if not args.config:
        parser.error("A config file is required")

    loaded_config = load_config(args.config)
    w3 = Web3(Web3.HTTPProvider(os.environ.get("WEB3_PROVIDER")))
    secondary_market_price_fetcher: SecondaryMarketPriceFetcher = OneInchPriceFetcher(
        os.getenv("ONE_INCH_API_KEY"), os.getenv("HTTP_PROXY")
    )
    if args.dry_run:
        data_saver: DataSaver = FakeDataSaver()
    else:
        data_saver: DataSaver = PostgresDataSaver(os.getenv("DATABASE_URL"))

    if not args.long_run:
        try:
            main(loaded_config, w3, secondary_market_price_fetcher, data_saver)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
    else:
        schedule.every(args.schedule).minutes.do(main, loaded_config, w3, secondary_market_price_fetcher, data_saver)
        logging.info(f"Started. Price fetching will run every {args.schedule} minutes.")
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                logging.error(f"An unexpected error occurred: {str(e)}")
            time.sleep(1)
