import { api } from "./client";
import { clearTokens, getRefreshToken, setTokens } from "./tokenStorage";
import type { Paginated, User } from "./types";

export interface LoginPayload {
  username: string;
  password: string;
  otp_code?: string;
  recovery_code?: string;
}

/** True when the backend's 400 response is the CustomTokenObtainPairSerializer's "needs a 2FA
 * code" case, not a genuine bad-credentials error — see accounts/serializers.py. */
export function is2FARequiredError(error: unknown): boolean {
  const data = (error as { response?: { data?: Record<string, unknown> } })?.response?.data;
  if (!data) return false;
  const otpError = data.otp_code;
  return Array.isArray(otpError) && otpError.some((m) => String(m).includes("2FA"));
}

export async function login(payload: LoginPayload): Promise<void> {
  const { data } = await api.post("/api/accounts/login/", payload);
  setTokens(data.access, data.refresh);
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/api/accounts/me/");
  return data;
}

export async function logout(): Promise<void> {
  const refresh = getRefreshToken();
  try {
    if (refresh) {
      await api.post("/api/accounts/logout/", { refresh });
    }
  } finally {
    clearTokens();
  }
}

export async function logoutAllDevices(): Promise<number> {
  const { data } = await api.post("/api/accounts/logout-all/");
  clearTokens();
  return data.sessions_invalidated as number;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
}

export async function register(payload: RegisterPayload): Promise<void> {
  await api.post("/api/accounts/register/", payload);
}

/** Admin/receptionist walk-in registration — same shape as public register, but role is forced
 * to `patient` server-side regardless of who calls it. */
export async function registerPatientByStaff(payload: RegisterPayload): Promise<User> {
  const { data } = await api.post<User>("/api/accounts/register/patient/", payload);
  return data;
}

export interface StaffCreatePayload extends RegisterPayload {
  role: "doctor" | "receptionist" | "lab_staff" | "admin";
}

export async function createStaffUser(payload: StaffCreatePayload): Promise<User> {
  const { data } = await api.post<User>("/api/accounts/staff/create/", payload);
  return data;
}

export async function listUsers(role?: string): Promise<User[]> {
  const { data } = await api.get<Paginated<User> | User[]>("/api/accounts/users/", {
    params: role ? { role } : undefined,
  });
  return Array.isArray(data) ? data : data.results;
}
