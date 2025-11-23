<template>
  <ClientOnly>
    <UModal
      v-model:open="internalOpen"
      title="New Alert"
      :close="{
        color: 'primary',
        variant: 'outline',
        class: 'rounded-full'
      }"
    >
      <template #body>
        <UAlert
          v-if="errorMessage"
          color="error"
          variant="soft"
          title="Unable to create alert"
          :description="errorMessage"
          class="mb-4"
        />
        <UForm class="space-y-4" @submit="submitAlert">
          <div class="grid gap-4 md:grid-cols-2">
            <UFormField
              label="Token name"
              required
              :hint="pricesError ? 'Unable to load tokens' : undefined"
            >
              <USelect
                v-model="form.token_name"
                :items="tokenOptions"
                placeholder="Select a token"
                size="lg"
                class="w-full"
                :disabled="submitting || pricesPending"
              />
            </UFormField>

            <UFormField label="Network" required>
              <USelect
                v-model="form.network"
                :items="networkOptions"
                placeholder="Select a network"
                size="lg"
                class="w-full"
                :disabled="submitting || !networkOptions.length"
              />
            </UFormField>
          </div>

          <UFormField label="Primary market" hint="Check if this alert targets the primary market.">
            <UCheckbox
              v-model="form.is_primary_market"
              label="Primary market"
              :disabled="submitting"
            />
          </UFormField>

          <div class="grid gap-4 md:grid-cols-3">
            <UFormField label="Metric" required>
              <USelect
                v-model="form.metric"
                :items="!form.is_primary_market ? metricDisplayOptions : metricPrimaryMarketOptions"
                size="xl"
                :disabled="submitting"
              />
            </UFormField>

            <UFormField label="Condition" required>
              <USelect
                v-model="form.condition"
                :items="conditionDisplayOptions"
                size="lg"
                :disabled="submitting"
              />
            </UFormField>

            <UFormField label="Threshold" required>
              <UInputNumber
                v-model="form.threshold"
                :format-options="{
                  signDisplay: payload.metric === 'premium' ? 'exceptZero' : 'auto',
                  minimumFractionDigits: payload.metric === 'premium' ? 2 : 4,
                }"
                :step="payload.metric === 'premium' ? 0.1 : 0.01"
                :min="payload.metric === 'price_eth' ? 0 : undefined"
                :default-value="1"
                size="lg"
                class="w-full"
                :disabled="submitting"
              />
            </UFormField>
          </div>

          <UFormField label="Type" required>
            <USelect
              v-model="form.type"
              :items="typeDisplayOptions"
              size="lg"
              :disabled="submitting"
            />
          </UFormField>

          <UButton
            block
            type="submit"
            color="primary"
            size="lg"
            :loading="submitting"
            icon="i-heroicons-check"
          >
            Create alert
          </UButton>
        </UForm>
      </template>
    </UModal>
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';

type MetricOption = 'price_eth' | 'premium';
type ConditionOption = 'lt' | 'lte' | 'eq' | 'gte' | 'gt';
type AlertType = 'one_off';

type MetricDisplayOption = 'Price (ETH)' | 'Premium (%)';
type ConditionDisplayOption = '<' | '≤' | '=' | '≥' | '>';
type AlertDisplayType = 'One-off';

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  'update:open': [value: boolean];
}>();

const toast = useToast();
const config = useRuntimeConfig();
const { authState } = useAuth();
const { prices, pending: pricesPending, error: pricesError, loadPrices } = usePrices();

const metricDisplayOptions: MetricDisplayOption[] = ["Price (ETH)", "Premium (%)"];
const metricPrimaryMarketOptions: MetricDisplayOption[] = ["Price (ETH)"];
const conditionDisplayOptions: ConditionDisplayOption[] = ["<", "≤", "=", "≥", ">"];
const typeDisplayOptions: AlertDisplayType[] = ["One-off"];

const metricDisplayToOptionMap: Record<MetricDisplayOption, MetricOption> = {
  "Price (ETH)": "price_eth",
  "Premium (%)": "premium",
};

const conditionDisplayToOptionMap: Record<ConditionDisplayOption, ConditionOption> = {
  "<": "lt",
  "≤": "lte",
  "=": "eq",
  "≥": "gte",
  ">": "gt",
};

const typeDisplayToOptionMap: Record<AlertDisplayType, AlertType> = {
  "One-off": "one_off",
};

const createDefaultFormValues = () => ({
  token_name: '',
  network: '',
  is_primary_market: false,
  metric: 'Price (ETH)' as MetricDisplayOption,
  condition: '<' as ConditionDisplayOption,
  threshold: 1,
  type: 'One-off' as AlertDisplayType,
});

const form = reactive<{
  token_name: string;
  network: string;
  is_primary_market: boolean;
  metric: MetricDisplayOption;
  condition: ConditionDisplayOption;
  threshold: number;
  type: AlertDisplayType;
}>(createDefaultFormValues());

type AlertPayload = {
  token_name: string;
  network: string;
  is_primary_market: boolean;
  metric: MetricOption;
  condition: ConditionOption;
  threshold: number;
  type: AlertType;
};

const payload = computed<AlertPayload>(() => ({
  token_name: form.token_name.trim(),
  network: uncapitalize(form.network.trim()),
  is_primary_market: form.is_primary_market,
  metric: metricDisplayToOptionMap[form.metric],
  condition: conditionDisplayToOptionMap[form.condition],
  threshold: Number(form.threshold),
  type: typeDisplayToOptionMap[form.type],
}));

const submitting = ref(false);
const errorMessage = ref('');
const tokenOptions = computed(() => {
  return Array.from(
    new Set((prices.value ?? []).map(token => token.token_name)),
  ).sort();
});

const networkOptions = computed(() => {
  if (!prices.value || !form.token_name) return [];
  let tokensForSelectedName = prices.value.filter(token => token.token_name === form.token_name);
  if (form.is_primary_market) {
    return Array.from(new Set(tokensForSelectedName.filter(token => token.is_primary_market).map(token => capitalize(token.network)))).sort();
  }
  else {
    return Array.from(new Set(tokensForSelectedName.map(token => capitalize(token.network)))).sort();
  }
});

const resetForm = () => {
  Object.assign(form, createDefaultFormValues());
  errorMessage.value = '';
};

const internalOpen = computed({
  get: () => props.open,
  set: (value: boolean) => emit('update:open', value),
});

watch(
  () => props.open,
  (open) => {
    if (!open) {
      setTimeout(() => resetForm(), 200);
      return;
    }

    loadPrices().catch(() => {
      // errors are surfaced via pricesError; noop here
    });
  },
);

watch(
  () => form.metric,
  (newMetric) => {
    // Reset threshold when metric changes
    form.threshold = metricDisplayToOptionMap[newMetric] === 'premium' ? 0 : 1;
  },
)

watch(
  networkOptions,
  (options) => {
    // Ensure the selected network always matches the chosen token
    if (form.network === '') {
      return;
    }

    if (!options.length) {
      form.network = '';
      return;
    }

    if (!options.includes(form.network)) {
      form.network = options[0] || '';
    }
  },
  { immediate: true },
);

watch(
  () => form.is_primary_market,
  () => {
    // Ensure the selected network always matches the chosen token
    if (!networkOptions.value.length) {
      form.network = '';
      return;
    }

    if (!networkOptions.value.includes(form.network)) {
      form.network = networkOptions.value[0] || '';
    }

    // Ensure metric is valid for primary market
    if (form.is_primary_market && form.metric === 'Premium (%)') {
      form.metric = 'Price (ETH)';
    }
  },
  { immediate: true },
)

const submitAlert = async () => {
  errorMessage.value = '';

  if (!authState.value.loggedIn || !authState.value.token?.access_token || !authState.value.email) {
    errorMessage.value = 'You must be logged in to create an alert.';
    return;
  }

  const thresholdMissing = form.threshold === null || form.threshold === undefined || Number.isNaN(Number(form.threshold));

  if (!form.token_name.trim() || !form.network.trim() || thresholdMissing) {
    errorMessage.value = 'Please fill in all required fields.';
    return;
  }

  submitting.value = true;
  try {
    const requestPayload = payload.value;

    await $fetch(`${config.public.apiBase}/alerts`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${authState.value.token.access_token}`,
      },
      body: {
        email: authState.value.email,
        ...requestPayload,
      },
    });

    toast.add({
      title: 'Alert created',
      color: 'success',
    });
    internalOpen.value = false;
  } catch (error: any) {
    errorMessage.value =
      error?.data?.detail ||
      error?.data?.message ||
      error?.message ||
      'Failed to create alert.';
  } finally {
    submitting.value = false;
  }
};
</script>
