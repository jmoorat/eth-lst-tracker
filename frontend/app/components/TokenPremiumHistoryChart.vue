<script setup lang="ts">
import type { ECBasicOption } from 'echarts/types/dist/shared';
import { use } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  DataZoomComponent,
  TitleComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import VChart from 'vue-echarts';
import { capitalize } from '~/utils/string';

use([LineChart, GridComponent, LegendComponent, TooltipComponent, DataZoomComponent, TitleComponent, CanvasRenderer]);

type HistoryResolution = '1d' | '1w' | '1m';

type PriceHistoryPoint = {
  timestamp: string;
  premium_percentage: number;
};

type PriceHistoryResponse = {
  prices: PriceHistoryPoint[];
};

const props = defineProps<{
  tokenName: string;
  networks: string[];
}>();

const resolutionOptions: Array<{ label: string; value: HistoryResolution; description: string }> = [
  { label: 'Daily', value: '1d', description: 'Daily buckets' },
  { label: 'Weekly', value: '1w', description: 'Weekly buckets' },
  { label: 'Monthly', value: '1m', description: 'Monthly buckets' },
];

const selectedResolution = ref<HistoryResolution>('1w');
const historyByNetwork = ref<Record<string, PriceHistoryPoint[]>>({});
const loading = ref(false);
const loadError = ref<string | null>(null);

const config = useRuntimeConfig();

const networkColorPalette: Record<string, string> = {
  ethereum: '#4f46e5',
  arbitrum: '#06bee0',
  base: '#007de3',
  bsc: '#f3ba2f',
  optimism: '#f95316',
  gnosis: '#22c55e',
  polygon: '#c955f7',
  zksync: '#6322d5',
};
const defaultThemePalette = ['#06b6d4', '#22c55e', '#a855f7', '#f97316', '#0ea5e9'];

const hasData = computed(() => {
  return props.networks.some(network => (historyByNetwork.value[network] ?? []).length > 0);
});

const fetchHistory = async () => {
  if (!props.networks.length) {
    historyByNetwork.value = {};
    return;
  }

  loading.value = true;
  loadError.value = null;

  try {
    const results = await Promise.all(
      props.networks.map(async network => {
        const response = await $fetch<PriceHistoryResponse>(
          `${config.public.apiBase}/prices/${props.tokenName}/history`,
          {
            params: {
              network,
              primary_market: false,
              resolution: selectedResolution.value,
            },
          },
        );

        return [network, response.prices] as const;
      }),
    );

    historyByNetwork.value = Object.fromEntries(results);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unable to load price history.';
    loadError.value = message;
  } finally {
    loading.value = false;
  }
};

watch([selectedResolution, () => props.networks], fetchHistory, { immediate: true });

const chartOptions = computed<ECBasicOption>(() => {
  const series = props.networks.map((network, index) => {
    const points = (historyByNetwork.value[network] ?? []).map(point => [point.timestamp, point.premium_percentage]);

    return {
      name: capitalize(network),
      type: 'line',
      showSymbol: false,
      smooth: true,
      emphasis: { focus: 'series' },
      lineStyle: { width: 2 },
      data: points,
      color: networkColorPalette[network] ?? defaultThemePalette[index % defaultThemePalette.length],
    };
  });

  return {
    textStyle: {
      color: '#e5e7eb',
    },
    grid: { top: 60, bottom: 60, left: 60, right: 20 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number | string) => `${Number(value).toFixed(2)}%`,
    },
    legend: {
      top: 10,
      textStyle: { color: '#e5e7eb' },
    },
    xAxis: {
      type: 'time',
      axisLabel: { color: '#9ca3af' },
      axisLine: { lineStyle: { color: '#4b5563' } },
      splitLine: { lineStyle: { color: 'rgba(75,85,99,0.3)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#9ca3af',
        formatter: (value: number) => `${value}%`,
      },
      splitLine: { lineStyle: { color: 'rgba(75,85,99,0.3)' } },
    },
    dataZoom: [
      { type: 'slider', bottom: 10, height: 14, backgroundColor: 'rgba(255,255,255,0.04)' },
    ],
    series,
  };
});
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-2xl font-semibold">Premium history</h2>
          <p class="text-sm text-gray-500">
            View the historical premium of {{ props.tokenName }} on secondary markets.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <UButton
            v-for="resolutionOption in resolutionOptions"
            :key="resolutionOption.value"
            size="xs"
            :color="selectedResolution === resolutionOption.value ? 'primary' : 'neutral'"
            :variant="selectedResolution === resolutionOption.value ? 'solid' : 'ghost'"
            @click="selectedResolution = resolutionOption.value"
          >
            {{ resolutionOption.label }}
          </UButton>
        </div>
      </div>
    </template>
    <div class="space-y-4">
      <UAlert
        v-if="loadError"
        color="error"
        variant="soft"
        title="Unable to load history"
        :description="loadError"
      />

      <div class="h-80">
        <ClientOnly>
          <USkeleton v-if="loading" class="h-full rounded-xl" />
          <div v-else-if="!hasData" class="flex h-full items-center justify-center text-gray-500 text-sm">
            No history data available for the selected filters.
          </div>
          <VChart
            v-else
            :option="chartOptions"
            autoresize
            class="h-full"
            :init-options="{ renderer: 'canvas' }"
          />
        </ClientOnly>
      </div>
    </div>
  </UCard>
</template>
