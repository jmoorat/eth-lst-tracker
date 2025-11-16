interface ApiToken {
  timestamp: string;
  token_name: string;
  network: string;
  is_primary_market: boolean;
  price_eth: number;
  premium_percentage: number;
}