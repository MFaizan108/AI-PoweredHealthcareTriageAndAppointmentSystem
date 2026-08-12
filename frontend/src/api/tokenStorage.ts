// Bearer tokens in localStorage (not an httpOnly cookie) — this matches the backend's existing
// design: every endpoint expects `Authorization: Bearer <token>`, not a session cookie, and the
// backend's CSP (settings.py SECURE_CSP) is the mitigation against the XSS/localStorage-theft risk
// that comes with this, same as any other bearer-token API.
const ACCESS_KEY = "healthcare_access_token";
const REFRESH_KEY = "healthcare_refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function setAccessToken(access: string): void {
  localStorage.setItem(ACCESS_KEY, access);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}
