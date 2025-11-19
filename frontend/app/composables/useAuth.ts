const TOKEN_STORAGE_KEY = 'ethlst_access_token';

interface StoredToken {
  access_token: string;
  expires_at: string;
}

export const useAuth = () => {
  const state = useState('auth', () => ({
    loggedIn: false,
    token: null as StoredToken | null,
  }));

  const loadFromStorage = () => {
    //if (!process.client) return;
    const raw = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as StoredToken;
      state.value.loggedIn = true;
      state.value.token = parsed;
    } catch {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  };

  const saveToken = (payload: StoredToken) => {
    //if (process.client) {
    //}
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(payload));
    state.value.loggedIn = true;
    state.value.token = payload;
  };

  const clearToken = () => {
    //if (process.client) {
    //}
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    state.value.loggedIn = false;
    state.value.token = null;
  };

  return {
    authState: state,
    loadFromStorage,
    saveToken,
    clearToken,
  };
};
