from collections import namedtuple
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy.sql import text


class QueryableTimeBucket(str, Enum):
    FIVE_MINUTES = "5 minutes"
    ONE_HOUR = "1 hour"
    ONE_DAY = "1 day"
    ONE_WEEK = "1 week"
    ONE_MONTH = "1 month"

interval_limits_per_time_buckets = {
    QueryableTimeBucket.FIVE_MINUTES: "1 day",
    QueryableTimeBucket.ONE_HOUR: "1 week",
    QueryableTimeBucket.ONE_DAY: "1 month",
    QueryableTimeBucket.ONE_WEEK: "6 months",
    QueryableTimeBucket.ONE_MONTH: "1 year"
}


def get_last_prices(db: Session):
    # db query custom SQL
    sql = text("""
        SELECT 
            last(timestamp, timestamp) as timestamp,
            token_name,
            last(price_eth, timestamp) as price_eth,
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
            last(price_eth, timestamp) as price_eth,
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


def get_price_history(db: Session, token_name: str, network: str, is_primary_market: bool, time_bucket: QueryableTimeBucket):
    sql = text("""
        SELECT
            time_bucket(:time_bucket, timestamp) as timestamp,
            avg(price_eth) as price_eth,
            round(avg(premium)*100, 3) as premium_percentage
        FROM prices
        WHERE timestamp > now() - INTERVAL :time_window
        AND token_name = :token_name AND network = :network AND is_primary_market = :is_primary_market
        GROUP BY timestamp, token_name, network, is_primary_market
        ORDER BY timestamp DESC;
    """)
    result = db.execute(sql, {
        'token_name': token_name,
        'network': network,
        'is_primary_market': is_primary_market,
        'time_bucket': time_bucket,
        'time_window': interval_limits_per_time_buckets[time_bucket]
    })
    Record = namedtuple('Record', result.keys())
    records = [Record(*r)._asdict() for r in result.fetchall()]
    return records

