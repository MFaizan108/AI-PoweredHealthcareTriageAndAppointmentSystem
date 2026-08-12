import { api } from "./client";

export interface PatientAnalytics {
  total_patients: number;
  new_patients_this_month: number;
  returning_patients: number;
  gender_distribution: Record<string, number>;
  age_distribution: Record<string, number>;
  department_utilization: Record<string, number>;
  patients_per_month: { month: string; count: number }[];
}

export interface AppointmentAnalytics {
  total_appointments: number;
  by_status: Record<string, number>;
  average_waiting_time_minutes: number | null;
  doctor_wise_appointments: { doctor_id: number; doctor__user__first_name: string; doctor__user__last_name: string; count: number }[];
  appointments_per_month: { month: string; count: number }[];
}

export interface AIAnalytics {
  total_assessments: number;
  by_urgency: Record<string, number>;
  emergency_escalations: number;
  clinician_reviewed_count: number;
  clinician_agreements: number;
  clinician_disagreements: number;
  ai_vs_clinician_agreement_rate_percent: number | null;
  note: string;
}

export async function getPatientAnalytics(): Promise<PatientAnalytics> {
  const { data } = await api.get<PatientAnalytics>("/api/analytics/patients/");
  return data;
}

export async function getAppointmentAnalytics(): Promise<AppointmentAnalytics> {
  const { data } = await api.get<AppointmentAnalytics>("/api/analytics/appointments/");
  return data;
}

export async function getAIAnalytics(): Promise<AIAnalytics> {
  const { data } = await api.get<AIAnalytics>("/api/analytics/ai/");
  return data;
}
