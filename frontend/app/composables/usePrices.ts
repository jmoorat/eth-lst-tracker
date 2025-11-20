const STALE_MS = 10 * 60 * 1000;

type PricesState = {
  data: ApiToken[] | null;
  fetchedAt: number;
};

export const usePrices = () => {
  const config = useRuntimeConfig();
  const state = useState<PricesState>('prices', () => ({ data: null, fetchedAt: 0 }));
  const pending = useState<boolean>('pricesPending', () => false);
  const error = useState<Error | null>('pricesError', () => null);

  const isStale = () => {
    if (!state.value.data) return true;
    return Date.now() - state.value.fetchedAt > STALE_MS;
  };

  const loadPrices = async (force = false) => {
    if (!force && !isStale()) {
      return state.value.data;
    }

    pending.value = true;
    error.value = null;

    try {
      const data = await $fetch<ApiToken[]>(`${config.public.apiBase}/prices`);
      state.value = { data, fetchedAt: Date.now() };
      return data;
    } catch (err) {
      error.value = err as Error;
      throw err;
    } finally {
      pending.value = false;
    }
  };

  const refresh = () => loadPrices(true);

  return {
    prices: computed(() => state.value.data),
    pending,
    error,
    loadPrices,
    refresh,
  };
};

