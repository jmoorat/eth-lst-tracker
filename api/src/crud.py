from collections import namedtuple

from sqlalchemy.orm import Session
from sqlalchemy.sql import text


def get_last_prices(db: Session):
    # db query custom SQL
    sql = text("""
        SELECT 
            last(timestamp, timestamp) as timestamp,
            token_name,last(price_eth, timestamp) as price_eth,
            network,
            is_primary_market,
            last(premium, timestamp)*100 as premium_percentage
        FROM prices
        GROUP BY token_name, network, is_primary_market
        ORDER BY token_name, is_primary_market DESC, network
    """)
    result = db.execute(sql)
    print(list(result.keys()))
    Record = namedtuple('Record', list(result.keys()))
    records = [Record(*r)._asdict() for r in result.fetchall()]
    print(records)
    return records


def get_last_price(db: Session, token_name: str, network: str, is_primary_market: bool):
    sql = text("""
        SELECT
            last(timestamp, timestamp) as timestamp,
            token_name,
            last(price_eth, timestamp) as price_eth,
            network,
            is_primary_market,
            last(premium, timestamp)*100 as premium_percentage
        FROM prices
        WHERE token_name = :token_name AND network = :network AND is_primary_market = :is_primary_market
        GROUP BY token_name, network, is_primary_market
        ORDER BY token_name, is_primary_market DESC, network
    """)
    result = db.execute(sql, {'token_name': token_name, 'network': network, 'is_primary_market': is_primary_market})
    Record = namedtuple('Record', result.keys())
    records = [Record(*r)._asdict() for r in result.fetchall()]
    if len(records) == 0:
        return None
    return records[0]


def get_price_history(db: Session, token_name: str, network: str, is_primary_market: bool):
    sql = text("""
        SELECT
            time_bucket('1 day', timestamp) as date,
            avg(price_eth) as average_price,
            round(avg(premium)*100, 3) as premium_percentage
        FROM prices
        WHERE timestamp > now() - INTERVAL '30 days'
        AND token_name = :token_name AND network = :network AND is_primary_market = :is_primary_market
        GROUP BY date, token_name, network, is_primary_market
        ORDER BY date DESC;
    """)
    result = db.execute(sql, {'token_name': token_name, 'network': network, 'is_primary_market': is_primary_market})
    Record = namedtuple('Record', result.keys())
    records = [Record(*r)._asdict() for r in result.fetchall()]
    return records

