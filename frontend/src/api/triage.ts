import { api } from "./client";
import type { EmergencyGuidance, Paginated, TriageAssessment } from "./types";

export interface TriageRequestPayload {
  symptoms_text: string;
  appointment?: number;
  use_ai_summary?: boolean;
}

export async function submitTriageAssessment(payload: TriageRequestPayload): Promise<TriageAssessment> {
  const { data } = await api.post<TriageAssessment>("/api/triage/assess/", payload);
  return data;
}

export async function getTriageAssessment(id: number): Promise<TriageAssessment> {
  const { data } = await api.get<TriageAssessment>(`/api/triage/assessments/${id}/`);
  return data;
}

export async function listTriageAssessments(params?: Record<string, string>): Promise<TriageAssessment[]> {
  const { data } = await api.get<Paginated<TriageAssessment> | TriageAssessment[]>("/api/triage/assessments/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function listEmergencyGuidance(): Promise<EmergencyGuidance[]> {
  const { data } = await api.get<Paginated<EmergencyGuidance> | EmergencyGuidance[]>("/api/triage/emergency-guidance/");
  return Array.isArray(data) ? data : data.results;
}

export interface AIProviderSettings {
  id: number;
  is_enabled: boolean;
  provider: "ollama" | "groq";
  ollama_base_url: string;
  ollama_model: string;
  groq_api_key_set: boolean;
  groq_model: string;
  timeout_seconds: number;
  updated_at: string;
}

export async function getAIProviderSettings(): Promise<AIProviderSettings> {
  const { data } = await api.get<AIProviderSettings>("/api/triage/ai-settings/");
  return data;
}

export interface UpdateAIProviderSettingsPayload {
  is_enabled?: boolean;
  provider?: "ollama" | "groq";
  ollama_base_url?: string;
  ollama_model?: string;
  groq_api_key?: string;
  groq_model?: string;
  timeout_seconds?: number;
}

export async function updateAIProviderSettings(payload: UpdateAIProviderSettingsPayload): Promise<AIProviderSettings> {
  const { data } = await api.patch<AIProviderSettings>("/api/triage/ai-settings/", payload);
  return data;
}
