import type { NavItem } from "../components/layout/Sidebar";

export const labStaffNavItems: NavItem[] = [
  { to: "/lab-staff", label: "Pending Tests", icon: "⌂" },
  { to: "/lab-staff/processing", label: "Processing", icon: "\u{2699}\u{FE0F}" },
  { to: "/lab-staff/reports", label: "Reports", icon: "\u{1F4C4}" },
];
