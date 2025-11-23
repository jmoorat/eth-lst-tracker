<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { capitalize } from '~/utils/string';

const { authState } = useAuth();
const config = useRuntimeConfig();
const toast = useToast();
const createModalOpen = ref(false);

const alerts = ref<ApiAlert[]>([]);
const loading = ref(false);
const errorMessage = ref('');
const deletingId = ref<string | null>(null);
const confirmAlertDeletionModalOpen = ref(false);
const alertPendingDelete = ref<ApiAlert | null>(null);

const metricLabels: Record<AlertMetric, string> = {
  price_eth: 'Price (ETH)',
  premium: 'Premium (%)',
};

const conditionLabels: Record<AlertCondition, string> = {
  lt: '<',
  lte: '≤',
  eq: '=',
  gte: '≥',
  gt: '>',
};

const statusLabels: Record<AlertStatus, string> = {
  active: 'Active',
  triggered: 'Triggered',
  paused: 'Paused',
  cancelled: 'Cancelled',
};

const statusColors: Record<AlertStatus, 'success' | 'warning' | 'info' | 'secondary'> = {
  active: 'success',
  triggered: 'warning',
  paused: 'info',
  cancelled: 'secondary',
};

const sortedAlerts = computed(() => {
  return [...alerts.value].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
});

const isLoggedIn = computed(() => authState.value.loggedIn && !!authState.value.token?.access_token);

const loadAlerts = async () => {
  if (!isLoggedIn.value) {
    alerts.value = [];
    return;
  }

  if (loading.value) {
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  try {
    const data = await $fetch<ApiAlert[]>(`${config.public.apiBase}/alerts`, {
      headers: {
        Authorization: `Bearer ${authState.value.token!.access_token}`,
      },
    });
    alerts.value = data;
  } catch (error: any) {
    errorMessage.value =
      error?.data?.detail ||
      error?.data?.message ||
      error?.message ||
      'Failed to load alerts.';
  } finally {
    loading.value = false;
  }
};

watch(
  () => authState.value.loggedIn,
  (loggedIn) => {
    if (loggedIn) {
      loadAlerts();
    } else {
      alerts.value = [];
      errorMessage.value = '';
    }
  },
  { immediate: true },
);

watch(
  confirmAlertDeletionModalOpen,
  (open) => {
    if (!open && !deletingId.value) {
      alertPendingDelete.value = null;
    }
  },
);

const formatThreshold = (alert: ApiAlert) => {
  if (alert.metric === 'premium') {
    return `${alert.threshold.toFixed(2)}%`;
  }
  return `${alert.threshold.toFixed(4)} ETH`;
};

const marketLabel = (alert: ApiAlert) => {
  return `${alert.is_primary_market ? 'Primary' : 'Secondary'} • ${capitalize(alert.network)}`;
};

const lastTriggeredLabel = (alert: ApiAlert) => {
  if (!alert.last_triggered_at) return 'Never triggered';
  return new Date(alert.last_triggered_at).toLocaleString();
};

const handleAlertCreated = async () => {
  await loadAlerts();
};

const openDeleteModal = (alert: ApiAlert) => {
  alertPendingDelete.value = alert;
  confirmAlertDeletionModalOpen.value = true;
};

const closeDeleteModal = () => {
  confirmAlertDeletionModalOpen.value = false;
  alertPendingDelete.value = null;
};

const confirmDelete = async () => {
  if (!isLoggedIn.value || deletingId.value || !alertPendingDelete.value) return;

  const alert = alertPendingDelete.value;
  deletingId.value = alert.id;
  try {
    await $fetch(`${config.public.apiBase}/alerts/${alert.id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${authState.value.token!.access_token}`,
      },
    });
    alerts.value = alerts.value.filter(a => a.id !== alert.id);
    toast.add({
      title: 'Alert deleted',
      color: 'success',
    });
  } catch (error: any) {
    toast.add({
      title: 'Failed to delete alert',
      description:
        error?.data?.detail ||
        error?.data?.message ||
        error?.message ||
        'Unable to delete alert.',
      color: 'error',
    });
  } finally {
    deletingId.value = null;
    closeDeleteModal();
  }
};
</script>

<template>
  <UCard class="min-h-96">
    <template #header>
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div class="space-y-2">
          <h1 class="text-3xl font-semibold">
            Alerts
          </h1>
          <p class="text-sm text-gray-500">
            View and manage email alerts for price and premium changes.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <UButton
              color="neutral"
              variant="soft"
              size="md"
              icon="i-heroicons-arrow-path"
              :disabled="!authState.loggedIn"
              :loading="loading"
              @click="loadAlerts"
          >
            Refresh
          </UButton>
          <UTooltip text="You must be logged in to create alerts" :delayDuration="300" :disabled="authState.loggedIn">
            <UButton
                color="primary"
                variant="solid"
                size="md"
                class="md:size-xl"
                icon="i-heroicons-plus"
                :disabled="!authState.loggedIn"
                @click="createModalOpen = true"
            >
              New Alert
            </UButton>
          </UTooltip>
        </div>
      </div>

    </template>
    <div class="flex flex-col gap-4">

      <UAlert
        v-if="errorMessage"
        color="error"
        variant="soft"
        title="Unable to load alerts"
        :description="errorMessage"
      />

      <div
        v-else-if="!authState.loggedIn"
        class="flex flex-col items-center justify-center gap-4 py-14 text-slate-500"
      >
        <UIcon name="i-heroicons-lock-closed" class="w-16 h-16" />
        <span class="text-base font-medium">Log in to see your alerts.</span>
      </div>

      <div v-else-if="loading" class="space-y-3">
        <USkeleton class="h-24 rounded-xl" v-for="n in 3" :key="n" />
      </div>

      <div
        v-else-if="!sortedAlerts.length"
        class="flex flex-col items-center justify-center w-full py-16 text-slate-700"
      >
        <UIcon name="i-heroicons-bell" class="w-24 h-24" />
        <span class="text-lg font-medium">No alerts</span>
        <p class="text-sm text-gray-500">Create your first alert to be notified.</p>
      </div>

      <div v-else class="space-y-3">
        <UCard
          v-for="alert in sortedAlerts"
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
                    @click="openDeleteModal(alert)"
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
  </UCard>
  <CreateAlertModal v-model:open="createModalOpen" @created="handleAlertCreated" />
  <UModal
    v-model:open="confirmAlertDeletionModalOpen"
    title="Delete alert"
    :close="{
      color: 'neutral',
      variant: 'outline',
      class: 'rounded-full'
    }"
  >
    <template #body>
      <p class="text-sm text-gray-300">
        Are you sure you want to delete this alert
        <span v-if="alertPendingDelete" class="font-semibold">
          for {{ alertPendingDelete.token_name }} ({{ marketLabel(alertPendingDelete) }}) on
          {{ metricLabels[alertPendingDelete.metric] }} {{ conditionLabels[alertPendingDelete.condition] }}
          {{ formatThreshold(alertPendingDelete) }}
        </span>
        ?
      </p>
      <div class="mt-6 flex justify-end gap-2">
        <UButton
          color="neutral"
          variant="ghost"
          @click="closeDeleteModal"
          :disabled="!!deletingId"
        >
          Cancel
        </UButton>
        <UButton
          color="error"
          icon="i-heroicons-trash"
          :loading="!!deletingId"
          :disabled="!!deletingId"
          @click="confirmDelete"
        >
          Delete
        </UButton>
      </div>
    </template>
  </UModal>
</template>
