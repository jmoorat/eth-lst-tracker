<script setup lang="ts">
import type { TableColumn } from '#ui/components/Table.vue';
import { getTokenFullName } from '~/utils/tokens';

const route = useRoute();
const tokenParam = computed(() => route.params.token_name as string);

const { prices, pending, error, refresh, loadPrices } = usePrices();
await loadPrices();

const isRefreshing = ref(false);

const tokensForName = computed<ApiToken[]>(() => {
  if (!prices.value) return [];
  return prices.value.filter(token => token.token_name === tokenParam.value);
});

const primaryToken = computed<ApiToken | null>(() => {
  if (!tokensForName.value.length) return null;
  return tokensForName.value.find(token => token.is_primary_market) ?? tokensForName.value[0]!;
});

const availableNetworks = computed<string[]>(() => {
  return Array.from(new Set(tokensForName.value.map(token => token.network)));
});

const secondaryMarkets = computed<ApiToken[]>(() => {
  return tokensForName.value.filter(token => !token.is_primary_market);
});

const columns: TableColumn<ApiToken>[] = [
  {
    accessorKey: 'network',
    header: 'Network',
    cell: ({row}) => capitalize(row.getValue('network')),
  },
  {
    accessorKey: 'price_eth',
    header: 'Price (ETH)',
    cell: ({ row }) => Number(row.getValue('price_eth')).toFixed(4),
  },
  {
    accessorKey: 'premium_percentage',
    header: 'Premium',
    cell: ({ row }) => `${Number(row.getValue('premium_percentage')).toFixed(2)}%`,
  },
] as const;

const tokenNotFound = computed(
  () => !pending.value && !error.value && tokensForName.value.length === 0,
);

const tokenTitle = computed(() => getTokenFullName(tokenParam.value));

const formatPrice = (price: number | null | undefined): string => {
  if (price === undefined || price === null) return 'N/A';
  return price.toFixed(4);
};

const availableNetworksLabel = computed(() => {
  // return capitalized network names separated by commas
  return availableNetworks.value
    .map(network => capitalize(network))
    .join(', ') || 'N/A';
});

const lastUpdatedLabel = computed(() => {
  if (!primaryToken.value) return 'N/A';
  return new Date(primaryToken.value.timestamp).toLocaleString();
});

const handleRefresh = async () => {
  if (isRefreshing.value) return;

  isRefreshing.value = true;
  try {
    await refresh();
  } finally {
    isRefreshing.value = false;
  }
};
</script>

<template>
  <div class="space-y-6">
    <UAlert
      v-if="error"
      color="error"
      variant="soft"
      title="Error while loading data"
      description="Unable to fetch token data. Please try again."
    >
      <template #actions>
        <UButton
          color="error"
          variant="outline"
          size="xs"
          :loading="isRefreshing"
          icon="i-heroicons-arrow-path"
          @click="handleRefresh"
        >
          Retry
        </UButton>
      </template>
    </UAlert>

    <div v-if="pending" class="space-y-4">
      <USkeleton class="h-32 rounded-2xl" />
      <USkeleton class="h-48 rounded-2xl" />
    </div>

    <UAlert
      v-else-if="tokenNotFound"
      color="secondary"
      variant="soft"
      title="Token not found"
      description="No data available for the specified token."
    />

    <template v-else>
      <UCard>
        <div class="flex flex-col gap-3">
          <p class="text-sm text-gray-500">Last update : {{ lastUpdatedLabel }}</p>
          <div>
            <h1 class="text-3xl font-semibold">
              {{ tokenTitle }}
              <span class="text-xl text-gray-500">({{ primaryToken?.token_name ?? tokenParam }})</span>
            </h1>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <p class="text-sm text-gray-500">Primary market price</p>
              <p class="text-2xl font-semibold">
                {{ primaryToken ? formatPrice(primaryToken.price_eth) : 'N/A' }} ETH
              </p>
            </div>
          </div>
          <p class="text-sm text-gray-500">
            Secondary markets available on :
            <span class="font-medium">{{ availableNetworksLabel }}</span>
          </p>
        </div>
      </UCard>

      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 class="text-2xl font-semibold">Secondary market prices per network</h2>
          <p class="text-sm text-gray-500">
            Each line represents a network on which the token is available to trade on the secondary market.
          </p>
        </div>
        <UButton :loading="isRefreshing" icon="i-heroicons-arrow-path" @click="handleRefresh">
          Refresh
        </UButton>
      </div>

      <UTable :data="secondaryMarkets" :columns="columns" />
    </template>
  </div>
</template>

<style scoped>

</style>
