<template>
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
        :disabled="!loggedIn"
        :loading="loading"
        @click="$emit('refresh')"
      >
        Refresh
      </UButton>
      <UTooltip text="You must be logged in to create alerts" :delayDuration="300" :disabled="loggedIn">
        <UButton
          color="primary"
          variant="solid"
          size="md"
          icon="i-heroicons-plus"
          :disabled="!loggedIn"
          @click="$emit('create')"
        >
          New Alert
        </UButton>
      </UTooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  loading: boolean;
  loggedIn: boolean;
}>();

defineEmits<{
  refresh: [];
  create: [];
}>();
</script>
