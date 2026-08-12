import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { createInvoice, createPayment, listInvoices } from "../../api/billing";
import { extractErrorMessage } from "../../api/client";
import type { Invoice, Patient } from "../../api/types";
import { PatientPicker } from "../../components/PatientPicker";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatCurrency, formatDateTime } from "../../format";

function NewInvoiceForm({ onCreated }: { onCreated: () => void }) {
  const queryClient = useQueryClient();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [description, setDescription] = useState("");
  const [consultationFee, setConsultationFee] = useState("0.00");
  const [labCharges, setLabCharges] = useState("0.00");
  const [discount, setDiscount] = useState("0.00");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => {
      if (!patient) throw new Error("Select a patient first.");
      return createInvoice({
        patient: patient.id,
        description,
        consultation_fee: consultationFee,
        lab_charges: labCharges,
        discount,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      setPatient(null);
      setDescription("");
      onCreated();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <Card title="New invoice">
      {error && <ErrorBanner message={error} />}
      <label className="field">
        <span>Patient</span>
        <PatientPicker value={patient} onChange={setPatient} />
      </label>
      <label className="field">
        <span>Description</span>
        <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      <div className="field-row">
        <label className="field">
          <span>Consultation fee</span>
          <input type="text" value={consultationFee} onChange={(e) => setConsultationFee(e.target.value)} />
        </label>
        <label className="field">
          <span>Lab charges</span>
          <input type="text" value={labCharges} onChange={(e) => setLabCharges(e.target.value)} />
        </label>
        <label className="field">
          <span>Discount</span>
          <input type="text" value={discount} onChange={(e) => setDiscount(e.target.value)} />
        </label>
      </div>
      <button className="btn btn-primary" disabled={!patient || createMutation.isPending} onClick={() => createMutation.mutate()}>
        {createMutation.isPending ? "Creating..." : "Create invoice"}
      </button>
    </Card>
  );
}

function RecordPaymentForm({ invoice, onDone }: { invoice: Invoice; onDone: () => void }) {
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState(invoice.balance_due);
  const [method, setMethod] = useState("cash");
  const [error, setError] = useState<string | null>(null);

  const payMutation = useMutation({
    mutationFn: () => createPayment({ invoice: invoice.id, amount, method, status: "success" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      onDone();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="report-block">
      {error && <ErrorBanner message={error} />}
      <div className="field-row">
        <label className="field">
          <span>Amount</span>
          <input type="text" value={amount} onChange={(e) => setAmount(e.target.value)} />
        </label>
        <label className="field">
          <span>Method</span>
          <select value={method} onChange={(e) => setMethod(e.target.value)}>
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="mobile_wallet">Mobile Wallet</option>
          </select>
        </label>
      </div>
      <button className="btn btn-primary" disabled={payMutation.isPending} onClick={() => payMutation.mutate()}>
        {payMutation.isPending ? "Recording..." : "Record payment"}
      </button>
    </div>
  );
}

export function AdminBillingPage() {
  const [showForm, setShowForm] = useState(false);
  const [payingFor, setPayingFor] = useState<number | null>(null);
  const invoices = useQuery({ queryKey: ["invoices", "all"], queryFn: () => listInvoices() });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Billing</h2>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Close" : "New invoice"}
        </button>
      </div>

      {showForm && <NewInvoiceForm onCreated={() => setShowForm(false)} />}

      <Card title="All invoices">
        {invoices.isLoading && <Spinner />}
        {invoices.isError && <ErrorBanner message="Could not load invoices." />}
        {!invoices.isLoading && (invoices.data ?? []).length === 0 && <EmptyState message="No invoices yet." />}
        {invoices.data?.map((inv) => (
          <div key={inv.id} className="list-row list-row-bordered" style={{ flexDirection: "column", alignItems: "stretch" }}>
            <div className="list-row" style={{ padding: 0 }}>
              <div>
                <div className="list-row-title">
                  {inv.patient_detail.user.first_name} {inv.patient_detail.user.last_name} &middot;{" "}
                  {inv.description || `Invoice #${inv.id}`}
                </div>
                <div className="list-row-subtitle">
                  {formatDateTime(inv.created_at)} &middot; Total {formatCurrency(inv.total_amount)} &middot; Due{" "}
                  {formatCurrency(inv.balance_due)}
                </div>
              </div>
              <div className="list-row-actions">
                <StatusBadge status={inv.status} />
                {inv.status !== "paid" && inv.status !== "cancelled" && (
                  <button className="btn btn-secondary" onClick={() => setPayingFor(payingFor === inv.id ? null : inv.id)}>
                    {payingFor === inv.id ? "Cancel" : "Record payment"}
                  </button>
                )}
              </div>
            </div>
            {payingFor === inv.id && <RecordPaymentForm invoice={inv} onDone={() => setPayingFor(null)} />}
          </div>
        ))}
      </Card>
    </div>
  );
}
