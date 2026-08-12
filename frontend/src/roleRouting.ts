import type { Role } from "./api/types";

const LANDING_PATH: Record<Role, string> = {
  patient: "/patient",
  doctor: "/doctor",
  receptionist: "/receptionist",
  lab_staff: "/lab-staff",
  admin: "/admin",
};

export function landingPathForRole(role: Role): string {
  return LANDING_PATH[role] ?? "/dashboard-pending";
}
