// Mirrors the DRF serializers in the Django backend (see docs/api.md for the full reference).
// Decimal fields (money) come back as strings from DRF's DecimalField — kept as `string` here
// rather than coerced to `number` to avoid float rounding on currency values.

export type Role = "admin" | "doctor" | "patient" | "receptionist" | "lab_staff";

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  phone_number: string;
  is_2fa_enabled: boolean;
  email_verified: boolean;
  date_joined: string;
}

export interface Patient {
  id: number;
  user: User;
  date_of_birth: string | null;
  gender: string;
  blood_group: string;
  address: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  known_allergies: string;
}

export interface Department {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

export interface Doctor {
  id: number;
  user: User;
  department: number | null;
  department_name: string;
  specialization: string;
  qualification: string;
  license_number: string;
  experience_years: number;
  consultation_fee: string;
  bio: string;
  is_active: boolean;
}

export type AppointmentStatus =
  | "pending"
  | "confirmed"
  | "in_consultation"
  | "completed"
  | "cancelled"
  | "no_show";

export interface Appointment {
  id: number;
  patient: number;
  patient_detail: Patient;
  doctor: number;
  doctor_detail: Doctor;
  appointment_date: string;
  slot_start_time: string;
  slot_end_time: string;
  status: AppointmentStatus;
  reason: string;
  token_number: string;
  booked_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface AvailableSlot {
  start_time: string;
  end_time: string;
  available: boolean;
}

export interface QueueEntry {
  token_number: string;
  patient: string;
  doctor: string;
  slot_start_time: string;
  status: AppointmentStatus;
  checked_in: boolean;
}

export interface Waitlist {
  id: number;
  patient: number;
  patient_detail: Patient;
  doctor: number;
  doctor_detail: Doctor;
  preferred_date: string;
  status: "waiting" | "notified" | "booked" | "cancelled";
  notes: string;
  created_at: string;
}

export interface Feedback {
  id: number;
  appointment: number;
  patient: number;
  patient_detail: Patient;
  doctor: number;
  doctor_detail: Doctor;
  rating: number;
  comment: string;
  created_at: string;
}

export type TriageUrgency = "low" | "moderate" | "high" | "emergency";
export type AISummaryStatus = "not_requested" | "pending" | "ready" | "failed";

export interface Symptom {
  id: number;
  name: string;
  category: string;
  keywords: string;
  severity_weight: number;
  red_flag: boolean;
  suggested_department: number | null;
  suggested_department_name: string | null;
}

export interface TriageAssessment {
  id: number;
  patient: number;
  patient_detail: Patient;
  appointment: number | null;
  symptoms_text: string;
  detected_symptoms: Symptom[];
  urgency: TriageUrgency;
  suggested_department: number | null;
  suggested_department_detail: Department | null;
  reasoning: string;
  ai_summary: string;
  ai_provider_used: string;
  ai_summary_error: string;
  ai_summary_status: AISummaryStatus;
  disclaimer: string;
  reviewed_by: number | null;
  clinician_agrees: boolean | null;
  clinician_notes: string;
  reviewed_at: string | null;
  created_at: string;
}

export interface EmergencyGuidance {
  id: number;
  urgency: TriageUrgency;
  title: string;
  content: string;
  emergency_numbers: string;
}

export interface Diagnosis {
  id: number;
  medical_record: number;
  description: string;
  diagnosed_at: string;
}

export interface MedicalRecord {
  id: number;
  patient: number;
  patient_detail: Patient;
  doctor: number;
  doctor_detail: Doctor;
  appointment: number | null;
  visit_date: string;
  consultation_notes: string;
  follow_up_date: string | null;
  follow_up_notes: string;
  diagnoses: Diagnosis[];
  created_at: string;
  updated_at: string;
}

export interface PrescriptionItem {
  id: number;
  prescription: number;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions: string;
}

export interface Prescription {
  id: number;
  patient: number;
  patient_detail: Patient;
  doctor: number;
  doctor_detail: Doctor;
  appointment: number | null;
  medical_record: number | null;
  notes: string;
  items: PrescriptionItem[];
  created_at: string;
}

export type LabTestStatus = "requested" | "sample_collected" | "processing" | "completed" | "cancelled";

export interface LabReport {
  id: number;
  lab_test: number;
  report_file: string | null;
  result_summary: string;
  uploaded_by: number | null;
  uploaded_at: string | null;
  reviewed_by_doctor: boolean;
  reviewed_at: string | null;
}

export interface LabTest {
  id: number;
  patient: number;
  patient_detail: Patient;
  requested_by: number;
  requested_by_detail: Doctor;
  appointment: number | null;
  test_name: string;
  notes: string;
  status: LabTestStatus;
  report: LabReport | null;
  requested_at: string;
  updated_at: string;
}

export type PaymentStatus = "pending" | "success" | "failed" | "refunded";

export interface Payment {
  id: number;
  invoice: number;
  amount: string;
  method: string;
  status: PaymentStatus;
  recorded_by: number | null;
  reference: string;
  created_at: string;
}

export type InvoiceStatus = "unpaid" | "partially_paid" | "paid" | "cancelled";

export interface Invoice {
  id: number;
  patient: number;
  patient_detail: Patient;
  appointment: number | null;
  lab_test: number | null;
  description: string;
  consultation_fee: string;
  lab_charges: string;
  discount: string;
  total_amount: string;
  status: InvoiceStatus;
  payments: Payment[];
  amount_paid: string;
  balance_due: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  appointment: number;
  sender: number;
  sender_detail: User;
  recipient: number;
  body: string;
  attachment: string | null;
  is_read: boolean;
  created_at: string;
}

export type NotificationType =
  | "appointment_booked"
  | "appointment_cancelled"
  | "prescription_available"
  | "general"
  | string;

export interface AppNotification {
  id: number;
  notification_type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface ApiErrorBody {
  detail?: string;
  [field: string]: unknown;
}
