import { api } from "./client";
import type { Invoice, Paginated, Payment } from "./types";

export async function listInvoices(params?: Record<string, string>): Promise<Invoice[]> {
  const { data } = await api.get<Paginated<Invoice> | Invoice[]>("/api/billing/", { params });
  return Array.isArray(data) ? data : data.results;
}

export interface CreateInvoicePayload {
  patient: number;
  appointment?: number;
  lab_test?: number;
  description?: string;
  consultation_fee?: string;
  lab_charges?: string;
  discount?: string;
}

export async function createInvoice(payload: CreateInvoicePayload): Promise<Invoice> {
  const { data } = await api.post<Invoice>("/api/billing/", payload);
  return data;
}

export interface CreatePaymentPayload {
  invoice: number;
  amount: string;
  method: string;
  status?: string;
  reference?: string;
}

export async function createPayment(payload: CreatePaymentPayload): Promise<Payment> {
  const { data } = await api.post<Payment>("/api/billing/payments/", payload);
  return data;
}
