<template>
  <div class="flex flex-col gap-4">
    <UAlert
      v-if="errorMessage"
      color="error"
      variant="soft"
      title="Unable to load alerts"
      :description="errorMessage"
    />

    <div
      v-else-if="!loggedIn"
      class="flex flex-col items-center justify-center gap-4 py-14 text-slate-500"
    >
      <UIcon name="i-heroicons-lock-closed" class="w-16 h-16" />
      <span class="text-base font-medium">Log in to see your alerts.</span>
    </div>

    <div v-else-if="loading" class="space-y-3">
      <USkeleton class="h-24 rounded-xl" v-for="n in 3" :key="n" />
    </div>

    <div
      v-else-if="!alerts.length"
      class="flex flex-col items-center justify-center w-full py-16 text-slate-700"
    >
      <UIcon name="i-heroicons-bell" class="w-24 h-24" />
      <span class="text-lg font-medium">No alerts</span>
      <p class="text-sm text-gray-500">Create your first alert to be notified.</p>
    </div>

    <div v-else class="space-y-3">
      <UCard
        v-for="alert in alerts"
        :key="alert.id"
        variant="soft"
      >
        <template #header>
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-lg font-semibold">{{ alert.token_name }}</p>
              <p class="text-sm text-gray-500">{{ marketLabel(alert) }}</p>
            </div>
            <div class="flex items-center gap-2">
              <UBadge :color="statusColors[alert.status]" variant="soft" size="lg">
                {{ statusLabels[alert.status] }}
              </UBadge>
              <UTooltip text="Delete alert">
                <UButton
                  color="error"
                  variant="ghost"
                  icon="i-heroicons-trash"
                  :loading="deletingId === alert.id"
                  :disabled="!!deletingId && deletingId !== alert.id"
                  @click="$emit('delete', alert)"
                />
              </UTooltip>
            </div>
          </div>
        </template>

        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p class="text-xs uppercase tracking-wide text-gray-400">Metric</p>
            <p class="text-sm font-medium">{{ metricLabels[alert.metric] }}</p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-wide text-gray-400">Condition</p>
            <p class="text-sm font-medium">
              {{ conditionLabels[alert.condition] }} {{ formatThreshold(alert) }}
            </p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-wide text-gray-400">Type</p>
            <p class="text-sm font-medium">One-off</p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-wide text-gray-400">Last triggered</p>
            <p class="text-sm font-medium">{{ lastTriggeredLabel(alert) }}</p>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  conditionLabels,
  formatThreshold,
  lastTriggeredLabel,
  marketLabel,
  metricLabels,
  statusColors,
  statusLabels,
} from '~/utils/alerts';

defineProps<{
  alerts: ApiAlert[];
  loading: boolean;
  errorMessage: string;
  loggedIn: boolean;
  deletingId: string | null;
}>();

defineEmits<{
  delete: [alert: ApiAlert];
}>();
</script>
