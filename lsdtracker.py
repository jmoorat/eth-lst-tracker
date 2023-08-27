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

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ.get("WEB3_PROVIDER")))
ONE_ETHER_STR: str = w3.to_wei(1, "ether")
DATABASE_URL = os.getenv("DATABASE_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HTTP_PROXY = os.getenv("HTTP_PROXY")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
ONE_INCH_API_KEY = os.getenv("ONE_INCH_API_KEY")
LONG_RUN = os.getenv("LONG_RUN", "false").lower() == "true"
SCHEDULE_MINUTES = int(os.getenv("SCHEDULE_MINUTES", "5"))

proxies = {"http": HTTP_PROXY, "https": HTTP_PROXY}

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


def load_config():
    """
    Loads config from config.json
    """
    with open("config.json") as f:
        return json.load(f)


def eth_price_to_string(eth_amount: int) -> str:
    """
    Converts an ETH amount in wei to a string
    """
    rem: int = eth_amount % 10**12
    return w3.from_wei(eth_amount - rem, "ether")


def get_secondary_market_rate(token_address: str, network: str) -> int:
    """
    Returns the secondary market rate for a token on a network

    Args:
        token_address (str): The token address
        network (str): The network to check

    Returns:
        int: The secondary market rate
    """
    time.sleep(1)  # 1inch API rate limit
    quote_params = {
        "src": token_address,
        "dst": config["chains"][network]["eth_token_address"],
        "amount": str(ONE_ETHER_STR),
    }
    url = f"https://api.1inch.dev/swap/v5.2/{config['chains'][network]['chain_id']}/quote?{requests.compat.urlencode(quote_params)}"

    try:
        response = requests.get(
            url, proxies=proxies, headers={"Authorization": ONE_INCH_API_KEY}
        )
    except Exception as e:
        logging.error(
            f"Failed to get secondary market rate for {token_address} on {network}: {str(e)}"
        )
        return -1

    if response.status_code != 200:
        logging.error(f"{response.status_code} error from 1inch: {response.reason}")
        return -1

    data = response.json()
    return int(data["toAmount"])


def get_premium(primary_market_price, secondary_market_price) -> float:
    """
    Returns the premium given a primary market price (benchmark price, Net asset value) and a secondary market price

    Args:
        primary_market_price (int): The primary market price (benchmark price)
        secondary_market_price (int): The secondary market price
    """
    return (secondary_market_price - primary_market_price) / primary_market_price


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
            network = "ethereum"
            contract = w3.eth.contract(
                address=token_address, abi=token["native_contract_abi"]
            )
            get_exchange_rate_function = contract.functions[
                token["get_exchange_rate_function_name"]
            ]
            primary_market_price = get_exchange_rate_function().call()
            if primary_market_price >= 0:
                logging.info(
                    f"Primary market price for {token['token_name']} on {network} is "
                    f"{eth_price_to_string(primary_market_price)} ETH"
                )
                save_data_to_db(
                    {
                        "timestamp": now,
                        "token_name": token["token_name"],
                        "price_eth": w3.from_wei(primary_market_price, "ether"),
                        "price_usd": None,
                        "network": network,
                        "is_primary_market": True,
                        "premium": 0,
                    }
                )

        for network in token["token_addresses"]:
            token_address = token["token_addresses"][network]
            price = get_secondary_market_rate(token_address, network)
            premium = get_premium(primary_market_price, price)

            if price >= 0:
                logging.info(
                    f"{token['token_name']} on {network} is {eth_price_to_string(price)} ETH -> "
                    f"{abs(premium * 100):.3f}% {'premium' if premium >= 0 else 'discount'}"
                )
                save_data_to_db(
                    {
                        "timestamp": now,
                        "token_name": token["token_name"],
                        "price_eth": w3.from_wei(price, "ether"),
                        "price_usd": None,
                        "network": network,
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
