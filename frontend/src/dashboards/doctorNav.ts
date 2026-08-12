import type { NavItem } from "../components/layout/Sidebar";

export const doctorNavItems: NavItem[] = [
  { to: "/doctor", label: "Today's Queue", icon: "⌂" },
  { to: "/doctor/appointments", label: "Appointments", icon: "\u{1F4C5}" },
  { to: "/doctor/patients", label: "Patients", icon: "\u{1F465}" },
  { to: "/doctor/records", label: "Medical Records", icon: "\u{1F4CB}" },
  { to: "/doctor/prescriptions", label: "Prescriptions", icon: "\u{1F48A}" },
  { to: "/doctor/lab-requests", label: "Lab Requests", icon: "\u{1F9EA}" },
  { to: "/doctor/availability", label: "Availability", icon: "\u{1F553}" },
  { to: "/doctor/messages", label: "Messages", icon: "\u{1F4AC}" },
  { to: "/doctor/activity", label: "My Activity", icon: "\u{1F4C8}" },
];
