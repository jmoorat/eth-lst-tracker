from collections import namedtuple

from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from . import models


def get_last_prices(db: Session):
    # db query custom SQL
    sql = text("""
        SELECT 
            last(timestamp, timestamp),
            token_name,last(price_eth, timestamp) as price_eth, network, is_primary_market, last(premium, timestamp)*100 as premium_percentage
        FROM prices
        GROUP BY token_name, network, is_primary_market
        ORDER BY token_name, is_primary_market DESC, network
    """)
    result = db.execute(sql)
    Record = namedtuple('Record', result.keys())
    records = [Record(*r) for r in result.fetchall()]
    return records


def get_last_price(db: Session, token_name: str, network: str, is_primary_market: bool):
    result = db.query(models.LsdPrice).filter(models.LsdPrice.token_name == token_name, models.LsdPrice.network == network, models.LsdPrice.is_primary_market == is_primary_market).order_by(models.LsdPrice.timestamp.desc()).first()
    return result


def get_price_history(db: Session, token_name: str, network: str, is_primary_market: bool, skip: int = 0, limit: int = 100):
    result = db.query(models.LsdPrice).filter(models.LsdPrice.token_name == token_name, models.LsdPrice.network == network, models.LsdPrice.is_primary_market == is_primary_market).order_by(models.LsdPrice.timestamp.desc()).offset(skip).limit(limit).all()
    return result

