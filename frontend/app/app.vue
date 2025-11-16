<template>
  <UApp>
    <UContainer class="py-12">
    <div class="space-y-10">
      <header class="text-center space-y-2">
        <NuxtLink to="/" class="inline-block">
          <Icon name="streamline:ethereum-circle-solid" class="w-12 h-12 text-primary-400 mb-2" />
          <h1 class="text-3xl font-semibold text-primary-400">ETH LST Tracker</h1>
        </NuxtLink>
        <p class="text-sm text-gray-400 max-w-2xl mx-auto">
          Track prices of the main Ethereum LSTs (Liquid Staking Tokens) and compare their premiums on secondary markets.
        </p>
      </header>
      <NuxtPage />
    </div>
  </UContainer>
  </UApp>
</template>

<script setup lang="ts">
</script>