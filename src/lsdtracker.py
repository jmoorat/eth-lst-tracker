import datetime
import json
import logging
import os
import sys
import time

import requests
import schedule
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Numeric, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from web3 import Web3

from adapters.OneInchPriceFetcher import OneInchPriceFetcher
from adapters.ParaswapPriceFetcher import ParaswapPriceFetcher
from ports.SecondaryMarketPriceFetcher import SecondaryMarketPriceFetcher
from src.utils import eth_price_to_string, get_premium, chains

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ.get("WEB3_PROVIDER")))
ONE_ETHER_STR: str = w3.to_wei(1, "ether")
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

# Initialize the secondary market price fetcher
price_fetcher: SecondaryMarketPriceFetcher = OneInchPriceFetcher(
    ONE_INCH_API_KEY, HTTP_PROXY
)


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


def load_config():
    """
    Loads config from config.json
    """
    with open("config.json") as f:
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


def main():
    primary_market_price = 0
    now = datetime.datetime.now()

    for token in config["lsd_tokens"]:
        if (
            "ethereum" in token["token_addresses"]
            and "native_contract_abi" in token
            and "get_exchange_rate_function_name" in token
        ):
            token_address = token["token_addresses"]["ethereum"]
            chain = "ethereum"
            contract = w3.eth.contract(
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
                        "price_eth": w3.from_wei(primary_market_price, "ether"),
                        "price_usd": None,
                        "network": chain,
                        "is_primary_market": True,
                        "premium": 0,
                    }
                )

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
                        "price_eth": w3.from_wei(price, "ether"),
                        "price_usd": None,
                        "network": chain,
                        "is_primary_market": False,
                        "premium": premium,
                    }
                )


config = load_config()

if __name__ == "__main__":
    if not LONG_RUN:
        main()
    else:
        schedule.every(SCHEDULE_MINUTES).minutes.do(main)
        while (LONG_RUN):
            schedule.run_pending()
            time.sleep(1)
