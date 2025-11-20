<template>
  <ClientOnly>
    <UModal
      v-model:open="internalOpen"
      title="Login"
      :close="{
        color: 'primary',
        variant: 'outline',
        class: 'rounded-full'
      }"
    >
      <template #body>
        <div class="space-y-4" v-if="!challengeSent">
          <UInput
            v-model="email"
            type="text"
            placeholder="you@example.com"
            size="xl"
            class="w-full"
            :disabled="sendingChallenge || verifyingCode"
          />

          <UButton
            block
            color="primary"
            :loading="sendingChallenge"
            :disabled="!email"
            @click="sendChallenge"
          >
            Send login code
          </UButton>
        </div>

        <div v-else class="space-y-4">
          <p class="text-sm">
            We sent a 6-digit code to {{ email }}. Enter it below to finish logging in.
          </p>
          <UInput
            v-model="code"
            type="text"
            placeholder="123456"
            size="xl"
            class="w-full"
            :disabled="verifyingCode"
          />

          <UButton
            block
            color="primary"
            :loading="verifyingCode"
            :disabled="code.trim().length !== 6"
            @click="verifyCode"
          >
            Verify code and login
          </UButton>
        </div>
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
const code = ref('');
const sendingChallenge = ref(false);
const challengeSent = ref(false);
const verifyingCode = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const resetState = () => {
  email.value = '';
  code.value = '';
  sendingChallenge.value = false;
  challengeSent.value = false;
  verifyingCode.value = false;
  errorMessage.value = '';
  successMessage.value = '';
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
  successMessage.value = '';
  try {
    await $fetch(`${config.public.apiBase}/auth/challenge`, {
      method: 'POST',
      body: {
        email: email.value,
      },
    });
    challengeSent.value = true;
    successMessage.value = 'Login code sent to your email address.';
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || error?.message || 'Failed to send login code.';
  } finally {
    sendingChallenge.value = false;
  }
};

const verifyCode = async () => {
  if (code.value.trim().length !== 6) return;
  verifyingCode.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  try {
    const response = await $fetch<{ access_token: string; expires_at: string }>(
      `${config.public.apiBase}/auth/login`,
      {
        method: 'POST',
        body: {
          email: email.value,
          code: code.value.trim(),
        },
      },
    );
    saveToken(response);
    emit('logged-in');
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || error?.message || 'Invalid code.';
  } finally {
    verifyingCode.value = false;
  }
};
</script>
