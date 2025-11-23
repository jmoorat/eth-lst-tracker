<script setup lang="ts">
import { ref } from 'vue';

const { authState } = useAuth();
const createModalOpen = ref(false);
</script>

<template>
  <UCard class="min-h-96">
    <div class="flex flex-col gap-3">
      <div class="flex items-start justify-between">
        <div class="space-y-2">
          <h1 class="text-3xl font-semibold">
            Alerts
          </h1>
        </div>
        <div class="self-start">
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
      <div class="flex items-center justify-center w-full py-16">
        <div class="flex flex-col items-center gap-3 text-slate-700">
          <UIcon name="i-heroicons-bell" class="w-24 h-24" />
          <span class="text-lg font-medium">No alerts</span>
        </div>
      </div>
    </div>
  </UCard>
  <CreateAlertModal v-model:open="createModalOpen" />
</template>
