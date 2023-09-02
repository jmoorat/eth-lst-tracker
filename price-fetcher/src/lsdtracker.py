import datetime
import json
import logging
import os
from argparse import ArgumentParser
import sys
import time
import schedule
from sqlalchemy import create_engine, Column, Numeric, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from web3 import Web3

from adapters.OneInchPriceFetcher import OneInchPriceFetcher
from adapters.ParaswapPriceFetcher import ParaswapPriceFetcher
from ports.SecondaryMarketPriceFetcher import SecondaryMarketPriceFetcher
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

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL) if not DRY_RUN else None

# Create a session factory
Session = sessionmaker(bind=engine) if not DRY_RUN else None

# Create a base class for declarative models
Base = declarative_base()


class LsdPriceModel(Base):
    """
    Represents a price of a token on a network at a given time in the database
    """

    __tablename__ = "prices"

    timestamp = Column(DateTime(timezone=True), primary_key=True)
    token_name = Column(String(10), primary_key=True)
    network = Column(String(20), primary_key=True)
    price_eth = Column(Numeric(20, 18))
    price_usd = Column(Numeric(16, 2))
    is_primary_market = Column(Boolean)
    premium = Column(Numeric(6, 5))


def load_config(config_file_path: str):
    """
    Loads config
    """
    with open(config_file_path) as f:
        return json.load(f)


def save_data_to_db(data) -> None:
    """
    Saves data to the database

    Args:
        data (dict): The data to save

    Returns:
        None
    """
    if not DRY_RUN:
        session = Session()
        try:
            # Create an instance of your model
            data_model = LsdPriceModel(**data)

            # Add the instance to the session
            session.add(data_model)

            # Commit the session to save the data
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error("Failed to save data:", str(e))
        finally:
            session.close()
    return


def main(
        config: dict,
        web3_provider: Web3,
        price_fetcher: SecondaryMarketPriceFetcher
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
                save_data_to_db(
                    {
                        "timestamp": now,
                        "token_name": token["token_name"],
                        "price_eth": web3_provider.from_wei(primary_market_price, "ether"),
                        "price_usd": None,
                        "network": chain,
                        "is_primary_market": True,
                        "premium": 0,
                    }
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
                save_data_to_db(
                    {
                        "timestamp": now,
                        "token_name": token["token_name"],
                        "price_eth": web3_provider.from_wei(price, "ether"),
                        "price_usd": None,
                        "network": chain,
                        "is_primary_market": False,
                        "premium": premium,
                    }
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

    if not LONG_RUN:
        main(loaded_config, w3, secondary_market_price_fetcher)
    else:
        schedule.every(SCHEDULE_MINUTES).minutes.do(main, loaded_config, w3, secondary_market_price_fetcher)
        while (LONG_RUN):
            schedule.run_pending()
            time.sleep(1)
