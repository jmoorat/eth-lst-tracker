<template>
  <UApp>
    <UContainer class="py-12">
    <div class="space-y-10">
      <header class="text-center space-y-2">
        <NuxtLink to="/">
          <div class="inline-flex flex-col items-center">
            <Logo class="w-24 h-24 text-primary-400 mb-2"/>
            <h1 class="text-3xl font-semibold text-primary-400">ETH LST Tracker</h1>
          </div>
        </NuxtLink>
        <p class="text-sm text-gray-400 max-w-2xl mx-auto">
          Track prices of the main Ethereum LSTs (Liquid Staking Tokens) and compare their premiums on secondary markets.
        </p>
        <UModal title="Login" v-model:open="isModalOpen" :close="{
        color: 'primary',
        variant: 'outline',
        class: 'rounded-full'
      }">
          <UButton label="Login" color="neutral" variant="subtle" v-if="!authState.loggedIn"/>

          <template #body>
            <div class="space-y-4" v-if="!challengeSent" >
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
              <p class="text-sm text-secondary">
                We sent a 6-digit code to {{ email }}. Enter it below to finish logging in.
              </p>
              <UInput
                v-model="code"
                type="text"
                placeholder="1234567"
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

            <UAlert
              v-if="successMessage"
              color="success"
              variant="soft"
            >
              {{ successMessage }}
            </UAlert>
            <UAlert
              v-if="errorMessage"
              color="error"
              variant="soft"
            >
              {{ errorMessage }}
            </UAlert>
          </template>
        </UModal>
      </header>
      <NuxtPage />
    </div>
  </UContainer>
  </UApp>
</template>

<script setup lang="ts">
const config = useRuntimeConfig();
const toast = useToast();
const { loadFromStorage, saveToken, authState } = useAuth();

const isModalOpen = ref(false);
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
  challengeSent.value = false;
  sendingChallenge.value = false;
  verifyingCode.value = false;
  errorMessage.value = '';
  successMessage.value = '';
};

onMounted(() => {
  loadFromStorage();
});

watch(() => isModalOpen.value, (open) => {
  if (!open) {
    resetState();
  }
});

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
    isModalOpen.value = false;
    toast.add({
      title: 'Successfully logged in!',
      type: 'foreground',
      color: 'success',
      duration: 5000,
    });
    resetState();

  } catch (error: any) {
    errorMessage.value = error?.data?.detail || error?.message || 'Invalid code.';
  } finally {
    verifyingCode.value = false;
  }
};


</script>
