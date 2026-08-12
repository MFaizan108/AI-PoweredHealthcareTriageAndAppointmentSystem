import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchCurrentUser, login as apiLogin, logout as apiLogout, type LoginPayload } from "../api/auth";
import { getAccessToken } from "../api/tokenStorage";
import type { User } from "../api/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return;
    }
    try {
      setUser(await fetchCurrentUser());
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));

    // Fired by api/client.ts when a refresh attempt fails (refresh token expired/blacklisted) —
    // the axios layer can't touch React state directly, so it broadcasts instead.
    const onSessionExpired = () => setUser(null);
    window.addEventListener("healthcare:session-expired", onSessionExpired);
    return () => window.removeEventListener("healthcare:session-expired", onSessionExpired);
  }, [refreshUser]);

  const login = useCallback(async (payload: LoginPayload) => {
    await apiLogin(payload);
    const freshUser = await fetchCurrentUser();
    setUser(freshUser);
    return freshUser;
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refreshUser }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
