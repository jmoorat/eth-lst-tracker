# ETH LST Tracker - Price Fetcher

A tool to fetch and store the primary and secondary market prices (and premium) of Ethereum's Liquid Staking Tokens (LSTs) on Ethereum and its layer-2s as well as other EVM networks.

## Features

- Fetches LSTs primary market prices directly from the native L1 token smart contracts
- Fetches LSTs secondary market prices from 1inch or Paraswap and compute premium/discount over the primary market price
- Supports multiple EVM networks and layer-2s (Ethereum, Arbitrum, Optimism, Base, Polygon, Gnosis)
- Saves data to TimescaleDB or PostgreSQL database
- Usable as a standalone CLI tool for one-off usage or as a long-running service to fetch prices periodically
- Dry-run mode without saving to the database

## Configuration

### Available command line arguments

| Argument                   | Environment variable | Description                                                                      | Required | Default value |
|----------------------------|----------------------|----------------------------------------------------------------------------------|----------|---------------|
| `-c`, `--config`           | -                    | Path to the token and network config file                                        | Yes      | -             |
| `-d`, `--dry-run`          | `DRY_RUN`            | Dry run mode without saving to database                                          | No       | `false`       |
| `-l`, `--long-run`         | `LONG_RUN`           | Continuous execution for periodically fetching prices                            | No       | `false`       |
| `-s`, `--schedule`         | `SCHEDULE`           | Duration in minutes between each price fetching operation (in long-running mode) | No       | `5`           |
| `-m`, `--secondary-market` | `SECONDARY_MARKET`   | Secondary market to use (`1inch` or `paraswap`)                                  | No       | `paraswap`    |
| `-w`, `--web3-provider`    | `WEB3_PROVIDER`      | Web3 provider URL (Infura or other)                                              | Yes      | -             |

### Available environment variables

| Variable           | Description               | Requis                                     | Default value |
|--------------------|---------------------------|--------------------------------------------|---------------|
| `DATABASE_URL`     | PostgreSQL connection URL | Yes (except in dry run mode)               | -             |
| `HTTP_PROXY`       | HTTP proxy URL            | No                                         | -             |
| `ONE_INCH_API_KEY` | 1inch API key             | No (if not using `1inch` secondary market) | -             |
| `LOG_LEVEL`        | Log level                 | No                                         | `INFO`        |

### Token and network configuration

The configuration file is a JSON file that defines the tokens and networks to be tracked. The structure of the configuration file is as follows:

```json
{
  "tokens": [
    {
      "token_name": "Token ticker",
      "token_addresses": {
        "network_name": "0x...",
        ...
      },
      "native_contract_abi": [...],
      "get_exchange_rate_function_name": "getExchangeRate"
    }
  ],
  ...
}
```

Here is a table explaining the fields that need to be configured for each token:

| Field                             | Description                                                                                                                                              |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `token_name`                      | The name of the token ticker (e.g `wstETH`)                                                                                                              |
| `token_addresses`                 | A dictionary mapping network names to token contract addresses.                                                                                          |
| `native_contract_abi`             | The ABI of the native token contract. A shortened ABI containing only the definition of the function retrieving the primary market rate can be provided. |
| `get_exchange_rate_function_name` | The name of the function to call on the native token contract to get the exchange rate.                                                                  |

A default configuration file is provided in the `config.json` file. You can modify it to add or remove tokens and networks as needed. All information about the tokens can be found on CoinMarketCap, Coingecko and the various blockchain explorers (for the ABI and exchange rate retrieval function name)

### Web3 provider
The Web3 provider URL can be set using the `WEB3_PROVIDER` environment variable and allows the price fetcher to query on-chain data.
This can be an Infura or Alchemy URL or any other Web3 provider URL.
The provider should support the networks you want to track.

### Secondary market
The price fetcher fetches the secondary market prices from decentralized exchanges (DEXs) APIs. Today only 1inch and Paraswap are supported.
Default is `paraswap` because 1inch API requires a paid subscription and an API key, but you can change it using the `SECONDARY_MARKET` environment variable or the `-m` command line argument.

