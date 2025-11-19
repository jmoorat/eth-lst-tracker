from collections import namedtuple

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

import models
import schemas
import schemas.price


def get_last_prices(db: Session):
    sql = text("""
        SELECT DISTINCT ON (token_name, network, is_primary_market)
               timestamp,
               token_name,
               network,
               is_primary_market,
               price_eth,
               premium * 100 AS premium_percentage
        FROM prices
        WHERE timestamp > now() - interval '7 days'
        ORDER BY token_name, network, is_primary_market, timestamp DESC
    """)
    result = db.execute(sql)
    record_cls = namedtuple("Record", list(result.keys()))
    records = [record_cls(*r)._asdict() for r in result.fetchall()]
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
    result = db.execute(
        sql,
        {
            "token_name": token_name,
            "network": network,
            "is_primary_market": is_primary_market,
        },
    )
    record_cls = namedtuple("Record", result.keys())
    records = [record_cls(*r)._asdict() for r in result.fetchall()]
    if not records:
        return None
    return records[0]


def get_price_history(
    db: Session,
    token_name: str,
    network: str,
    is_primary_market: bool,
    advanced: bool,
    time_bucket: schemas.price.QueryableTimeBucket,
):
    if advanced:
        sql = text("""
           SELECT
               time_bucket(:time_bucket, timestamp) as time_bucket,

               min(price_eth) as min_price_eth,
               max(price_eth) as max_price_eth,
               avg(price_eth) as avg_price_eth,
               first(price_eth, timestamp) as first_price_eth,
               last(price_eth, timestamp) as last_price_eth,

               round(min(premium)*100, 3) as min_premium_percentage,
               round(max(premium)*100, 3) as max_premium_percentage,
               round(avg(premium)*100, 3) as avg_premium_percentage,
               round(first(premium, timestamp)*100, 3) as first_premium_percentage,
               round(last(premium, timestamp)*100, 3) as last_premium_percentage

           FROM prices
           WHERE timestamp
               > now() - INTERVAL :time_window
             AND token_name = :token_name
             AND network = :network
             AND is_primary_market = :is_primary_market
           GROUP BY time_bucket, token_name, network, is_primary_market
           ORDER BY time_bucket DESC;
           """)
    else:
        sql = text("""
            SELECT
                time_bucket(:time_bucket, timestamp) as time_bucket,
                avg(price_eth) as price_eth,
                round(avg(premium)*100, 3) as premium_percentage
            FROM prices
            WHERE timestamp > now() - INTERVAL :time_window
            AND token_name = :token_name AND network = :network AND is_primary_market = :is_primary_market
            GROUP BY time_bucket, token_name, network, is_primary_market
            ORDER BY time_bucket DESC;
        """)
    result = db.execute(
        sql,
        {
            "token_name": token_name,
            "network": network,
            "is_primary_market": is_primary_market,
            "time_bucket": time_bucket,
            "time_window": schemas.price.interval_limits_per_time_buckets[time_bucket],
        },
    )
    record_cls = namedtuple("Record", result.keys())
    records = [record_cls(*r)._asdict() for r in result.fetchall()]
    return records


def get_available_tokens_and_networks(db: Session):
    return db.query(models.TokenListing).all()
