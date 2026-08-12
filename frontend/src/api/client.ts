import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./tokenStorage";

export const api = axios.create({ baseURL: "/" });

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refreshing is rotated server-side (ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION — see
// docs/authentication.md), so only one refresh call may be in flight at a time or the second
// request's refresh token would already be blacklisted by the first. Concurrent 401s share one
// in-flight refresh promise instead of each firing their own.
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = getRefreshToken();
  if (!refresh) {
    throw new Error("No refresh token available");
  }
  const { data } = await axios.post("/api/accounts/login/refresh/", { refresh });
  setTokens(data.access, data.refresh);
  return data.access as string;
}

function broadcastLoggedOut() {
  clearTokens();
  window.dispatchEvent(new Event("healthcare:session-expired"));
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const isAuthEndpoint = original?.url?.includes("/api/accounts/login");

    if (error.response?.status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true;
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const newAccess = await refreshPromise;
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch {
        broadcastLoggedOut();
      }
    }

    return Promise.reject(error);
  },
);

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data === "string") return data;
    if (data && typeof data === "object") {
      const parts = Object.entries(data).map(([key, value]) => {
        const text = Array.isArray(value) ? value.join(" ") : String(value);
        return key === "detail" || key === "non_field_errors" ? text : `${key}: ${text}`;
      });
      if (parts.length) return parts.join(" ");
    }
    if (error.message) return error.message;
  }
  return "Something went wrong. Please try again.";
}
