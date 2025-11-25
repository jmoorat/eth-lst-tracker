<template>
  <ClientOnly>
    <UModal
      v-model:open="internalOpen"
      title="Log in"
      :close="{
        color: 'primary',
        variant: 'outline',
        class: 'rounded-full'
      }"
    >
      <template #body>
        <UAlert v-if="errorMessage" color="error" variant="soft" title="Oops" :description="errorMessage " class="mb-4" />
        <UForm class="space-y-4" v-if="!challengeSent" @submit="sendChallenge">
          <UFormField label="Email Address" required>
            <UInput
              v-model="email"
              type="text"
              placeholder="you@example.com"
              size="xl"
              class="w-full"
              :disabled="sendingChallenge || verifyingCode"
            />
          </UFormField>

          <UButton
            block
            color="primary"
            icon="i-heroicons-envelope"
            :loading="sendingChallenge"
            :disabled="!email"
            type="submit"
          >
            Send authentication code
          </UButton>
        </UForm>

        <UForm v-else class="space-y-4" @submit="verifyCode">
          <p class="text-sm">
            We sent a 6-digit code to {{ email }}. Enter it below to finish logging in.
          </p>
          <UFormField required>
            <div class="flex justify-center">
              <UPinInput
                v-model="code"
                :length="6"
                type="number"
                size="xl"
                :disabled="verifyingCode"
                otp
              />
            </div>
          </UFormField>

          <UButton
            block
            color="primary"
            icon="i-heroicons-check"
            :loading="verifyingCode"
            :disabled="code.length !== 6"
            type="submit"
          >
            Verify code and login
          </UButton>
        </UForm>
      </template>
    </UModal>
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  'update:open': [value: boolean];
  'logged-in': [];
}>();

const config = useRuntimeConfig();
const { saveToken } = useAuth();

const internalOpen = computed({
  get: () => props.open,
  set: (value: boolean) => emit('update:open', value),
});

const email = ref('');
const code = ref([]);
const sendingChallenge = ref(false);
const challengeSent = ref(false);
const verifyingCode = ref(false);
const errorMessage = ref('');

const resetState = () => {
  email.value = '';
  code.value = [];
  sendingChallenge.value = false;
  challengeSent.value = false;
  verifyingCode.value = false;
  errorMessage.value = '';
};

watch(
  () => props.open,
  (open) => {
    if (!open) {
      setTimeout(() => {
        resetState();
      }, 300);
    }
  },
);

const sendChallenge = async () => {
  if (!email.value) return;
  sendingChallenge.value = true;
  errorMessage.value = '';
  try {
    await $fetch(`${config.public.apiBase}/auth/challenge`, {
      method: 'POST',
      body: {
        email: email.value,
      },
    });
    challengeSent.value = true;
  } catch (error: any) {
    errorMessage.value = error?.data?.detail[0]?.msg || error?.data?.detail || 'Failed to send login code.';
  } finally {
    sendingChallenge.value = false;
  }
};

const verifyCode = async () => {
  if (code.value.length !== 6) return;
  verifyingCode.value = true;
  errorMessage.value = '';
  try {
    const response = await $fetch<{ access_token: string; expires_at: string }>(
      `${config.public.apiBase}/auth/login`,
      {
        method: 'POST',
        body: {
          email: email.value,
          code: code.value.join('').trim(),
        },
      },
    );
    saveToken(response);
    emit('logged-in');
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || error?.detail || 'Invalid code.';
  } finally {
    verifyingCode.value = false;
  }
};
</script>
