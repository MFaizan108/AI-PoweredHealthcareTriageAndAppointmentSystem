import type { NavItem } from "../components/layout/Sidebar";

export const adminNavItems: NavItem[] = [
  { to: "/admin", label: "Overview", icon: "⌂" },
  { to: "/admin/users", label: "Users", icon: "\u{1F464}" },
  { to: "/admin/doctors", label: "Doctors", icon: "\u{1FA7A}" },
  { to: "/admin/patients", label: "Patients", icon: "\u{1F465}" },
  { to: "/admin/departments", label: "Departments", icon: "\u{1F3E5}" },
  { to: "/admin/appointments", label: "Appointments", icon: "\u{1F4C5}" },
  { to: "/admin/billing", label: "Billing", icon: "\u{1F4B3}" },
  { to: "/admin/analytics", label: "AI Analytics", icon: "\u{1F4C8}" },
  { to: "/admin/audit-logs", label: "Audit Logs", icon: "\u{1F510}" },
  { to: "/admin/settings", label: "System Settings", icon: "\u{2699}\u{FE0F}" },
];
