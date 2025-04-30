# ETH LST Tracker

## Overview

ETH LST Tracker is a tool to track the primary and secondary market prices of Ethereum's Liquid Staking Tokens (LSTs) on Ethereum and its layer-2s as well as other EVM networks.
This tool allows identifying arbitrage opportunities between primary and secondary markets on Ethereum and other networks as well as simply identifying premiums or discounts before buying or selling LSTs on secondary markets.

## Features
- Easily configurable to track tokens on different networks (rebasable tokens like stETH are not supported)
- Supports for different secondary market sources (1inch, Paraswap)
- Price fetcher can be used as a standalone CLI tool for one-off usage
- REST API to provide easy access to the latest and historical data on different timeframes

## Getting Started

### Prerequisites

- Python 3.13 or higher
- UV package manager (optional but recommended)
- Docker and Docker Compose (for running the price fetcher and API services in containers)
- TimescaleDB or a PostgreSQL database configured with TimescaleDB extension for data storage

### Database configuration

You can either use the TimescaleDB Docker image used in the docker-compose file or set up a TimescaleDB database on your own.
If you choose to set up your own instance, make sur to create a database with the TimescaleDB extension enabled and the prices table as defined in the `database/prices.sql` file.

### Setup with the provided Docker compose file (including a TimescaleDB instance)

1. Clone the repository:
2. Configure price fetcher (you can find configuration details in the `price-fetcher/README.md` file):
   1. Configure tokens and networks to track in the `price-fetcher/config.json` file.
   2. Provide a Web3 provider URL in the `docker-compose.yml` file. You can use Infura or any other Web3 provider.
   3. Provide a PostgreSQL connection URL in the `docker-compose.yml` or use the default one declared in the file.
3. Configure the API:
   1. Provide a PostgreSQL connection URL in the `docker-compose.yml` or use the default one declared in the file.
4. Build and run the Docker containers:
```bash
docker-compose up --build
```
5. Access the API at `http://localhost:3000` (or the port you specified in the docker-compose file).
6. Access the API documentation at `http://localhost:3000/docs`.
7. Access logs with `docker-compose logs -f` command.
