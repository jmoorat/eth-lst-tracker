const TOKEN_STORAGE_KEY = 'ethlst_access_token';

interface StoredToken {
  access_token: string;
  expires_at: string;
}

interface JwtPayload {
  sub?: string;
}

const isExpired = (expiresAt: string) => {
  const expiresAtMs = new Date(expiresAt).getTime();
  return Number.isNaN(expiresAtMs) || expiresAtMs <= Date.now();
};

const decodeEmailFromToken = (token: string | null) => {
  if (!token) {
    return null;
  }

  const parts = token.split('.');
  if (parts.length < 2 || typeof atob !== 'function') {
    return null;
  }

  if (!parts[1]) {
    return null;
  }

  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padLength = (4 - (base64.length % 4)) % 4;
    const padded = base64 + '='.repeat(padLength);
    const decoded = atob(padded);
    const payload = JSON.parse(decoded) as JwtPayload;
    return typeof payload.sub === 'string' ? payload.sub : null;
  } catch {
    return null;
  }
};

export const useAuth = () => {
  const state = useState('auth', () => ({
    loggedIn: false,
    token: null as StoredToken | null,
    email: null as string | null,
  }));

  const loadFromStorage = () => {
    //if (!process.client) return;
    const raw = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as StoredToken;
      if (isExpired(parsed.expires_at)) {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        return;
      }
      state.value.loggedIn = true;
      state.value.token = parsed;
      state.value.email = decodeEmailFromToken(parsed.access_token);
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
    state.value.email = decodeEmailFromToken(payload.access_token);
  };

  const clearToken = () => {
    //if (process.client) {
    //}
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    state.value.loggedIn = false;
    state.value.token = null;
    state.value.email = null;
  };

  return {
    authState: state,
    loadFromStorage,
    saveToken,
    clearToken,
  };
};
