type AlertMetric = 'price_eth' | 'premium';
type AlertCondition = 'lt' | 'lte' | 'gt' | 'gte' | 'eq';
type AlertType = 'one_off';
type AlertStatus = 'active' | 'triggered' | 'paused' | 'cancelled';

interface ApiAlert {
  id: string;
  email: string;
  token_name: string;
  network: string;
  is_primary_market: boolean;
  metric: AlertMetric;
  condition: AlertCondition;
  threshold: number;
  type: AlertType;
  status: AlertStatus;
  trigger_count: number;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
  last_triggered_at: string | null;
}
