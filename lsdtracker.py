import os
import requests
from web3 import Web3
import json
import time
from sqlalchemy import create_engine, Column, Numeric, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ.get("WEB3_PROVIDER")))
ONE_ETHER_STR: str = w3.to_wei(1, "ether")
ETH_ADDRESS = os.getenv("ETH_ADDRESS")
WETH_ADDRESS_POLYGON = os.getenv("WETH_ADDRESS_POLYGON")
DATABASE_URL = os.getenv("DATABASE_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CHAIN_ID_MAPPING = {
    "ethereum": 1,
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10
}

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a base class for declarative models
Base = declarative_base()

class LsdPriceModel(Base):
    """
    Represents a price of a token on a network at a given time in the database
    """
    __tablename__ = 'prices'

    timestamp = Column(DateTime(timezone=True), primary_key=True)
    token_name = Column(String(10), primary_key=True)
    network = Column(String(20), primary_key=True)
    price_eth = Column(Numeric(20, 18))
    price_usd = Column(Numeric(16, 2))
    is_primary_market = Column(Boolean)
    premium = Column(Numeric(6, 5))

def load_config():
    """
    Loads config from lsd.json
    """
    with open('lsd.json') as f:
        return json.load(f)

def eth_price_to_sting(r) -> str:
    """
    Converts a rate to a string
    """
    rem = r % 10**12
    return w3.from_wei(r - rem, 'ether')

def get_secondary_market_rate(token_address: str, network: str) -> int:
    """
    Returns the secondary market rate for a token on a network

    Args:
        token_address (str): The token address
        network (str): The network to check

    Returns:
        int: The secondary market rate
    """
    quote_params = {
        'fromTokenAddress': token_address,
        'toTokenAddress': ETH_ADDRESS if network != "polygon" else WETH_ADDRESS_POLYGON,
        'amount': str(ONE_ETHER_STR)
    }
    url = f"https://api.1inch.io/v5.0/{CHAIN_ID_MAPPING[network]}/quote?{requests.compat.urlencode(quote_params)}"
    response = requests.get(url)

    if response.status_code != 200:
        logging.error(f"{response.status_code} error from 1inch: {response.reason}")
        return 0

    data = response.json()
    return int(data['toTokenAmount'])

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

def main():
    tokens_config = load_config()
    primary_market_price = 0
    now = datetime.datetime.now()

    for token in tokens_config:
        if "ethereum" in token["token_addresses"] and "native_contract_abi" in token and "get_exchange_rate_function_name" in token:
                token_address = token["token_addresses"]["ethereum"]
                network = "ethereum"
                contract = w3.eth.contract(address=token_address, abi=token["native_contract_abi"])
                get_exchange_rate_function = contract.functions[token["get_exchange_rate_function_name"]]
                primary_market_price = get_exchange_rate_function().call()
                logging.info(f"Primary market price for {token['token_name']} on {network} is {eth_price_to_sting(primary_market_price)} ETH")

                save_data_to_db({
                    'timestamp': now,
                    'token_name': token['token_name'],
                    'price_eth': w3.from_wei(primary_market_price, "ether"),
                    'price_usd': None,
                    'network': network,
                    'is_primary_market': True,
                    'premium': 0
                })

        for network in token["token_addresses"]:
            token_address = token["token_addresses"][network]
            price = get_secondary_market_rate(token_address, network)
            premium = get_premium(primary_market_price, price)
            logging.info(f"{token['token_name']} on {network} is {eth_price_to_sting(price)} ETH -> {abs(premium*100):.3f}% {'premium' if premium >= 0 else 'discount'}")

            save_data_to_db({
                'timestamp': now,
                'token_name': token['token_name'],
                'price_eth': w3.from_wei(price, "ether"),
                'price_usd': None,
                'network': network,
                'is_primary_market': False,
                'premium': premium
            })


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    logging.info(f"Time taken: {end_time - start_time:.2f} seconds")
