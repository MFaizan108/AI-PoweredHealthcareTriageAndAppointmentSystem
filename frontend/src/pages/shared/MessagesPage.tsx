import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { listAppointments } from "../../api/appointments";
import { extractErrorMessage } from "../../api/client";
import { listMessages, markMessageRead, sendMessage } from "../../api/messaging";
import type { Appointment } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

function Thread({ appointmentId }: { appointmentId: number }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);

  const messages = useQuery({
    queryKey: ["messages", appointmentId],
    queryFn: () => listMessages(appointmentId),
    refetchInterval: 10_000,
  });

  useEffect(() => {
    const unreadIncoming = messages.data?.filter((m) => !m.is_read && m.recipient === user?.id) ?? [];
    unreadIncoming.forEach((m) => {
      markMessageRead(m.id).then(() => queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] }));
    });
    // Only depends on the message list identity changing — re-running per render would re-fire marks.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages.data]);

  const sendMutation = useMutation({
    mutationFn: () => sendMessage({ appointment: appointmentId, body }),
    onSuccess: () => {
      setBody("");
      queryClient.invalidateQueries({ queryKey: ["messages", appointmentId] });
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="thread">
      {messages.isLoading && <Spinner />}
      <div className="thread-messages">
        {messages.data?.map((m) => (
          <div key={m.id} className={`thread-bubble${m.sender === user?.id ? " thread-bubble-mine" : ""}`}>
            <div className="thread-bubble-meta">
              {m.sender_detail.first_name || m.sender_detail.username} &middot; {formatDateTime(m.created_at)}
            </div>
            <div>{m.body}</div>
          </div>
        ))}
        {!messages.isLoading && (messages.data ?? []).length === 0 && <EmptyState message="No messages yet — say hello." />}
      </div>
      {error && <ErrorBanner message={error} />}
      <form
        className="thread-composer"
        onSubmit={(e) => {
          e.preventDefault();
          if (body.trim()) sendMutation.mutate();
        }}
      >
        <input type="text" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Type a message..." />
        <button type="submit" className="btn btn-primary" disabled={sendMutation.isPending}>
          Send
        </button>
      </form>
    </div>
  );
}

function counterpartLabel(appointment: Appointment, viewerIsDoctor: boolean): string {
  if (viewerIsDoctor) {
    const p = appointment.patient_detail.user;
    return `${p.first_name || p.username} ${p.last_name}`.trim();
  }
  const d = appointment.doctor_detail.user;
  return `Dr. ${d.first_name} ${d.last_name}`.trim();
}

export function MessagesPage() {
  const { user } = useAuth();
  const viewerIsDoctor = user?.role === "doctor";
  const appointments = useQuery({ queryKey: ["appointments"], queryFn: () => listAppointments() });
  const [selected, setSelected] = useState<number | null>(null);

  const conversations = [...(appointments.data ?? [])].sort((a, b) =>
    `${b.appointment_date}`.localeCompare(`${a.appointment_date}`),
  );

  return (
    <div className="page-stack">
      <h2 className="page-heading">Messages</h2>
      <p className="muted-text">Conversations are scoped to an appointment between patient and doctor.</p>

      <div className="messages-layout">
        <Card title="Conversations" className="messages-list-card">
          {appointments.isLoading && <Spinner />}
          {!appointments.isLoading && conversations.length === 0 && <EmptyState message="No appointments to message about yet." />}
          {conversations.map((a) => (
            <button
              key={a.id}
              className={`conversation-item${selected === a.id ? " conversation-item-active" : ""}`}
              onClick={() => setSelected(a.id)}
            >
              <div className="list-row-title">{counterpartLabel(a, viewerIsDoctor)}</div>
              <div className="list-row-subtitle">{a.appointment_date}</div>
            </button>
          ))}
        </Card>

        <Card title="Conversation" className="messages-thread-card">
          {selected ? <Thread appointmentId={selected} /> : <EmptyState message="Select a conversation to view messages." />}
        </Card>
      </div>
    </div>
  );
}
