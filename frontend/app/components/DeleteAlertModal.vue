<template>
  <UModal
    v-model:open="internalOpen"
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
        <span v-if="alert" class="font-semibold">
          for {{ alert.token_name }} ({{ marketLabel(alert) }}) on
          {{ metricLabels[alert.metric] }} {{ conditionLabels[alert.condition] }}
          {{ formatThreshold(alert) }}
        </span>
        ?
      </p>
      <div class="mt-6 flex justify-end gap-2">
        <UButton
          color="neutral"
          variant="ghost"
          @click="emit('update:open', false)"
          :disabled="busy"
        >
          Cancel
        </UButton>
        <UButton
          color="error"
          icon="i-heroicons-trash"
          :loading="busy"
          :disabled="busy"
          @click="emit('confirm')"
        >
          Delete
        </UButton>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  conditionLabels,
  formatThreshold,
  marketLabel,
  metricLabels,
} from '~/utils/alerts';

const props = defineProps<{
  open: boolean;
  alert: ApiAlert | null;
  busy: boolean;
}>();

const emit = defineEmits<{
  'update:open': [value: boolean];
  confirm: [];
}>();

const internalOpen = computed({
  get: () => props.open,
  set: (value: boolean) => emit('update:open', value),
});
</script>
