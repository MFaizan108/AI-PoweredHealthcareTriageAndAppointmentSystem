import { useQuery } from "@tanstack/react-query";
import { listInvoices } from "../../api/billing";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatCurrency, formatDateTime } from "../../format";

export function BillingPage() {
  const invoices = useQuery({ queryKey: ["invoices"], queryFn: () => listInvoices() });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Billing</h2>

      {invoices.isLoading && <Spinner />}
      {invoices.isError && <ErrorBanner message="Could not load invoices." />}
      {!invoices.isLoading && (invoices.data ?? []).length === 0 && <EmptyState message="No invoices yet." />}

      {invoices.data?.map((inv) => (
        <Card key={inv.id} title={inv.description || `Invoice #${inv.id}`} actions={<StatusBadge status={inv.status} />}>
          <p className="muted-text">{formatDateTime(inv.created_at)}</p>
          <table className="data-table">
            <tbody>
              <tr>
                <td>Consultation fee</td>
                <td>{formatCurrency(inv.consultation_fee)}</td>
              </tr>
              <tr>
                <td>Lab charges</td>
                <td>{formatCurrency(inv.lab_charges)}</td>
              </tr>
              <tr>
                <td>Discount</td>
                <td>-{formatCurrency(inv.discount)}</td>
              </tr>
              <tr className="data-table-total">
                <td>Total</td>
                <td>{formatCurrency(inv.total_amount)}</td>
              </tr>
              <tr>
                <td>Paid</td>
                <td>{formatCurrency(inv.amount_paid)}</td>
              </tr>
              <tr className="data-table-total">
                <td>Balance due</td>
                <td>{formatCurrency(inv.balance_due)}</td>
              </tr>
            </tbody>
          </table>

          {inv.payments.length > 0 && (
            <>
              <h3 className="card-subtitle">Payment history</h3>
              <ul className="plain-list">
                {inv.payments.map((p) => (
                  <li key={p.id}>
                    {formatCurrency(p.amount)} via {p.method} &mdash; <StatusBadge status={p.status} /> &middot;{" "}
                    {formatDateTime(p.created_at)}
                  </li>
                ))}
              </ul>
            </>
          )}
        </Card>
      ))}
    </div>
  );
}
