import { capitalize } from '~/utils/string';

export const metricLabels: Record<AlertMetric, string> = {
  price_eth: 'Price (ETH)',
  premium: 'Premium (%)',
};

export const conditionLabels: Record<AlertCondition, string> = {
  lt: '<',
  lte: '≤',
  eq: '=',
  gte: '≥',
  gt: '>',
};

export const statusLabels: Record<AlertStatus, string> = {
  active: 'Active',
  triggered: 'Triggered',
  paused: 'Paused',
  cancelled: 'Cancelled',
};

export const statusColors: Record<AlertStatus, 'success' | 'warning' | 'info' | 'secondary'> = {
  active: 'success',
  triggered: 'warning',
  paused: 'info',
  cancelled: 'secondary',
};

export const formatThreshold = (alert: ApiAlert) => {
  if (alert.metric === 'premium') {
    return `${alert.threshold.toFixed(2)}%`;
  }
  return `${alert.threshold.toFixed(4)} ETH`;
};

export const marketLabel = (alert: ApiAlert) => {
  return `${alert.is_primary_market ? 'Primary' : 'Secondary'} • ${capitalize(alert.network)}`;
};

export const lastTriggeredLabel = (alert: ApiAlert) => {
  if (!alert.last_triggered_at) return 'Never triggered';
  return new Date(alert.last_triggered_at).toLocaleString();
};
