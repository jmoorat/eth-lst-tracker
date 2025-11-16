<script setup lang="ts">
import { getTokenFullName } from '~/utils/tokens';


interface TokenRow extends ApiToken {
  secondary_markets_count: number;
  fullName: string;
}

const config = useRuntimeConfig();

const { data: apiData, pending, error, refresh } = await useFetch<ApiToken[]>(
  `${config.public.apiBase}/prices`,
);

const filteredTokens = computed<TokenRow[]>(() => {
  if (!apiData.value) return [];

  const primaryTokens = apiData.value.filter(
    token => token.is_primary_market && token.network === 'ethereum',
  );

  const secondaryPremiums = apiData.value
    .filter(token => !token.is_primary_market && token.network === 'ethereum')
    .reduce((acc, token) => {
      acc[token.token_name] = token.premium_percentage;
      return acc;
    }, {} as Record<string, number>);

  const secondaryMarketCounts = apiData.value
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
<NuxtLink
  v-for="token in filteredTokens"
  :key="token.token_name"
  :to="`/tokens/${token.token_name}`"
>
  <UCard class="mb-4 transition-colors hover:!bg-gray-800" variant="soft">
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
