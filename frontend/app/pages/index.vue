<script setup lang="ts">
import { getTokenFullName } from '~/utils/tokens';

interface TokenRow extends ApiToken {
  secondary_markets_count: number;
  fullName: string;
}

const { prices, pending, error, refresh, loadPrices } = usePrices();
await loadPrices();

const filteredTokens = computed<TokenRow[]>(() => {
  if (!prices.value) return [];

  const primaryTokens = prices.value.filter(
    token => token.is_primary_market && token.network === 'ethereum',
  );

  const secondaryPremiums = prices.value
    .filter(token => !token.is_primary_market && token.network === 'ethereum')
    .reduce((acc, token) => {
      acc[token.token_name] = token.premium_percentage;
      return acc;
    }, {} as Record<string, number>);

  const secondaryMarketCounts = prices.value
    .filter(token => !token.is_primary_market)
    .reduce((acc, token) => {
      acc[token.token_name] = (acc[token.token_name] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

  return primaryTokens.map(token => ({
    ...token,
    premium_percentage: secondaryPremiums[token.token_name] ?? token.premium_percentage,
    secondary_markets_count: secondaryMarketCounts[token.token_name] || 0,
    fullName: getTokenFullName(token.token_name),
  }));
});

const formatPrice = (price: number): string => {
  return price.toFixed(4);
};

const formatPremium = (premium: number): string => {
  return premium.toFixed(2);
};
</script>

<template>
  <UAlert v-if="error" color="error" variant="soft" class="mb-4">
    <template #title>
      Error loading tokens
    </template>
    {{ error.message || error }}
  </UAlert>

  <div v-else-if="pending">
    <USkeleton class="h-32 mb-4" v-for="n in 3" :key="n" />
  </div>

  <template v-else>
    <NuxtLink
      v-for="token in filteredTokens"
      :key="token.token_name"
      :to="`/tokens/${token.token_name}`"
    >
      <UCard class="mb-4 transition-colors hover:!bg-elevated" variant="subtle">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-xl font-semibold">{{ token.fullName }} ({{ token.token_name }})</h2>
          </div>
          <div class="text-right">
            <p class="text-lg font-medium">Price: {{ formatPrice(token.price_eth) }} ETH</p>
            <p
              class="text-sm"
              :class="token.premium_percentage >= 0 ? 'text-green-600' : 'text-red-600'"
            >
              Premium: {{ formatPremium(token.premium_percentage) }}%
            </p>
            <p class="text-sm text-gray-500">
              Secondary markets available: {{ token.secondary_markets_count }}
            </p>
          </div>
        </div>
      </UCard>
    </NuxtLink>
  </template>
</template>
