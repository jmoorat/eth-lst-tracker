export const tokenNamesMap = {
  rETH: 'RocketPool ETH',
  wstETH: 'Lido Wrapped staked ETH',
  sfrxETH: 'Frax staked ETH',
  wBETH: 'Binance staked ETH',
  cbETH: 'Coinbase staked ETH',
} as const;

export const getTokenFullName = (tokenName: string): string => {
  return tokenNamesMap[tokenName as keyof typeof tokenNamesMap] ?? tokenName;
};