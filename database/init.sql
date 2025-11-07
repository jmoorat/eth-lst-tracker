CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

---
/* Create prices hypertable */
CREATE TABLE IF NOT EXISTS prices
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

CREATE INDEX IF NOT EXISTS prices_token_network_market_timestamp_idx ON prices (token_name, network, is_primary_market, timestamp DESC);

---
/* Create token listings table */
CREATE TABLE IF NOT EXISTS token_listings (
    token_name       text    NOT NULL,
    network          text    NOT NULL,
    is_primary_market boolean NOT NULL,
    PRIMARY KEY (token_name, network, is_primary_market)
);

/* Trigger function to upsert into token_listings on insert into prices */
CREATE OR REPLACE FUNCTION upsert_token_listings()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO token_listings (token_name, network, is_primary_market)
    VALUES (NEW.token_name, NEW.network, NEW.is_primary_market)
    ON CONFLICT (token_name, network, is_primary_market) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_upsert_token_listings
AFTER INSERT ON prices
FOR EACH ROW
EXECUTE FUNCTION upsert_token_listings();
