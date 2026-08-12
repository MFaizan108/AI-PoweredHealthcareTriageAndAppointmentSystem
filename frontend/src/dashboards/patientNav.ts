import type { NavItem } from "../components/layout/Sidebar";

export const patientNavItems: NavItem[] = [
  { to: "/patient", label: "Overview", icon: "⌂" },
  { to: "/patient/appointments", label: "Appointments", icon: "\u{1F4C5}" },
  { to: "/patient/triage", label: "AI Triage", icon: "\u{1FA7A}" },
  { to: "/patient/records", label: "Medical Records", icon: "\u{1F4CB}" },
  { to: "/patient/prescriptions", label: "Prescriptions", icon: "\u{1F48A}" },
  { to: "/patient/lab-reports", label: "Lab Reports", icon: "\u{1F9EA}" },
  { to: "/patient/billing", label: "Billing", icon: "\u{1F4B3}" },
  { to: "/patient/messages", label: "Messages", icon: "\u{1F4AC}" },
  { to: "/patient/notifications", label: "Notifications", icon: "\u{1F514}" },
];
