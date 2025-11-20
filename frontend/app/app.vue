<template>
  <UApp>
    <UContainer class="py-10">
      <div class="space-y-10">
        <header class="relative space-y-2">
          <div class="absolute top-0 right-0 flex items-center gap-2">
            <UTooltip :text="authState.loggedIn ? 'Log out' : 'Log in'">
              <UButton
                :icon="authState.loggedIn ? 'i-heroicons-arrow-right-on-rectangle' : 'i-heroicons-arrow-left-on-rectangle'"
                size="md"
                color="primary"
                variant="ghost"
                @click="authState.loggedIn ? handleLogout() : openLoginModal()"
              />
            </UTooltip>
          </div>

          <div class="text-center space-y-2">
            <NuxtLink to="/">
              <div class="inline-flex flex-col items-center">
                <Logo class="w-24 h-24 text-primary-400 mb-2" />
                <h1 class="text-3xl font-semibold text-primary-400">
                  ETH LST Tracker
                </h1>
              </div>
            </NuxtLink>
          </div>

          <p class="text-sm text-gray-400 max-w-2xl mx-auto text-center">
            Track prices of the main Ethereum LSTs (Liquid Staking Tokens) and compare their premiums on secondary markets.
          </p>
        </header>

        <NuxtPage />
      </div>
    </UContainer>

    <LoginModal v-model:open="loginModalOpen" @logged-in="handleLoggedIn" />
  </UApp>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';

const toast = useToast();
const { authState, loadFromStorage, clearToken } = useAuth();

const loginModalOpen = ref(false);

onMounted(() => {
  loadFromStorage();
});

const openLoginModal = () => {
  loginModalOpen.value = true;
};

const handleLogout = () => {
  clearToken();
  toast.add({
    title: 'Logged out',
    color: 'neutral',
  });
};

const handleLoggedIn = () => {
  toast.add({
    title: 'Successfully logged in!',
    color: 'success',
  });
  loginModalOpen.value = false;
};
</script>
