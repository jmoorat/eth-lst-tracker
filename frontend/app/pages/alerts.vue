<script setup lang="ts">
import { computed, ref, watch } from 'vue';

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

const handleAlertCreated = async () => {
  toast.add({
    title: 'Alert created',
    color: 'success',
  });
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
      <AlertsToolbar
        :loading="loading"
        :logged-in="authState.loggedIn"
        @refresh="loadAlerts"
        @create="createModalOpen = true"
      />
    </template>

    <AlertsList
      :alerts="sortedAlerts"
      :loading="loading"
      :error-message="errorMessage"
      :logged-in="authState.loggedIn"
      :deleting-id="deletingId"
      @delete="openDeleteModal"
    />
  </UCard>

  <CreateAlertModal v-model:open="createModalOpen" @created="handleAlertCreated" />
  <DeleteAlertModal
    v-model:open="confirmAlertDeletionModalOpen"
    :alert="alertPendingDelete"
    :busy="!!deletingId"
    @confirm="confirmDelete"
  />
</template>
