CREATE EXTENSION IF NOT EXISTS timescaledb;

---
/* Create prices hypertable */
create table prices
(
    timestamp         timestamp with time zone default now() not null,
    token_name        text                                   not null,
    price_eth         numeric(20, 18),
    price_usd         numeric(16, 2),
    network           text                                   not null,
    is_primary_market boolean                                not null,
    premium           numeric(6, 5),
    primary key (timestamp, token_name, network, is_primary_market)
);
SELECT create_hypertable('prices', 'timestamp');