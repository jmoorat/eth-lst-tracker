import datetime
import json
import logging
import os
import sys
import time
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import schedule
from web3 import Web3

from data_storage.DataSaver import DataSaver, FailedToSaveDataPointException
from data_storage.FakeDataSaver import FakeDataSaver
from data_storage.PostgresDataSaver import PostgresDataSaver
from price_fetcher.OneInchPriceFetcher import OneInchPriceFetcher
from price_fetcher.ParaswapPriceFetcher import ParaswapPriceFetcher
from price_fetcher.SecondaryMarketPriceFetcher import (
    CannotGetPriceException,
    SecondaryMarketPriceFetcher,
    UnsupportedChainException,
    UnsupportedTokenException,
)
from utils import SecondaryMarket, chains, eth_price_to_string, get_premium

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


def get_env_or_default_or_required(env_key: str, default_value: Optional[str] = None) -> dict:
    env_value = os.getenv(env_key)

    if env_value is not None and env_value != "":
        return {"default": env_value}
    if default_value is not None:
        return {"default": default_value}

    return {"required": True}


def main(
    config: dict,
    web3_provider: Web3,
    price_fetcher: SecondaryMarketPriceFetcher,
    data_saver: DataSaver,
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
            contract = web3_provider.eth.contract(address=token_address, abi=token["native_contract_abi"])
            get_exchange_rate_function = contract.functions[token["get_exchange_rate_function_name"]]
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
            except (
                UnsupportedChainException,
                UnsupportedTokenException,
                CannotGetPriceException,
            ) as e:
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
                        premium=premium,
                    )
                except FailedToSaveDataPointException as e:
                    logging.error(f"Failed to save data point: {str(e)}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", help="config file path", required=True)
    parser.add_argument(
        "-d",
        "--dry-run",
        help="dry run (fetched data won't be saved)",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--long-run",
        help="long run (data will be fetched at regular intervals)",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--schedule",
        help="Number of minutes to wait between each run (when using long-run mode)",
        type=int,
        **get_env_or_default_or_required("SCHEDULE", "5"),
    )
    parser.add_argument(
        "-m",
        "--secondary-market",
        help="Secondary market to use",
        type=SecondaryMarket,
        choices=list(SecondaryMarket),
        **get_env_or_default_or_required("SECONDARY_MARKET", SecondaryMarket.PARASWAP),
    )
    parser.add_argument(
        "-w",
        "--web3-provider",
        help="Web3 provider URL",
        type=str,
        **get_env_or_default_or_required("WEB3_PROVIDER"),
    )
    args = parser.parse_args()

    # Load config
    loaded_config = load_config(args.config)

    # Setup web3 provider
    w3 = Web3(Web3.HTTPProvider(args.web3_provider))

    # Setup secondary market price fetcher
    if args.secondary_market == SecondaryMarket.PARASWAP:
        secondary_market_price_fetcher: SecondaryMarketPriceFetcher = ParaswapPriceFetcher(os.getenv("HTTP_PROXY"))
    else:
        secondary_market_price_fetcher: SecondaryMarketPriceFetcher = OneInchPriceFetcher(
            os.getenv("ONE_INCH_API_KEY"), os.getenv("HTTP_PROXY")
        )

    # Setup data saver
    if args.dry_run or os.getenv("DRY_RUN") == "true":
        data_saver: DataSaver = FakeDataSaver()
    else:
        data_saver: DataSaver = PostgresDataSaver(os.getenv("DATABASE_URL"))

    # Launch
    if args.long_run or os.getenv("LONG_RUN") == "true":
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="price-fetcher")

        def run_main_job():
            try:
                main(loaded_config, w3, secondary_market_price_fetcher, data_saver)
            except Exception as e:
                logging.error(f"An unexpected error occurred while running the job: {str(e)}")

        def schedule_run():
            executor.submit(run_main_job)

        schedule.every(args.schedule).minutes.at(":00").do(schedule_run)
        logging.info(f"Started. Price fetching will run every {args.schedule} minutes.")

        try:
            while True:
                try:
                    schedule.run_pending()
                except Exception as e:
                    logging.error(f"An unexpected error occurred while scheduling: {str(e)}")

                idle_seconds = schedule.idle_seconds()
                if idle_seconds is None:
                    idle_seconds = 1
                else:
                    idle_seconds = max(0, idle_seconds)
                time.sleep(idle_seconds)
        except KeyboardInterrupt:
            logging.info("Stopping scheduler after receiving keyboard interrupt.")
        finally:
            executor.shutdown(wait=True)
    else:
        try:
            main(loaded_config, w3, secondary_market_price_fetcher, data_saver)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
