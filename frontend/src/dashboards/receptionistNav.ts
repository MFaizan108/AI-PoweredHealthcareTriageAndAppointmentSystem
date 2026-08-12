import type { NavItem } from "../components/layout/Sidebar";

export const receptionistNavItems: NavItem[] = [
  { to: "/receptionist", label: "Queue", icon: "⌂" },
  { to: "/receptionist/register", label: "Walk-in Registration", icon: "\u{1F4DD}" },
  { to: "/receptionist/patients", label: "Patient Search", icon: "\u{1F50D}" },
  { to: "/receptionist/appointments", label: "Appointments", icon: "\u{1F4C5}" },
];
