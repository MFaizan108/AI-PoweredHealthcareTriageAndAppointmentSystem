import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { createAvailability, deleteAvailability, listAvailability, listDoctors } from "../../api/doctors";
import { extractErrorMessage } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";

const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function DoctorAvailabilityPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [weekday, setWeekday] = useState(0);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [slotMinutes, setSlotMinutes] = useState(20);
  const [error, setError] = useState<string | null>(null);

  // No dedicated "my doctor profile" endpoint — DoctorViewSet has no `me` action (only
  // patients/me exists), so the current doctor's own profile is found by matching user id
  // against the (small, already-scoped) doctors list rather than adding a backend endpoint
  // just for this one lookup.
  const doctors = useQuery({ queryKey: ["doctors"], queryFn: () => listDoctors() });
  const myDoctor = doctors.data?.find((d) => d.user.id === user?.id);

  const availability = useQuery({
    queryKey: ["availability", myDoctor?.id],
    queryFn: () => listAvailability(myDoctor!.id),
    enabled: Boolean(myDoctor),
  });

  const createMutation = useMutation({
    mutationFn: () => {
      if (!myDoctor) throw new Error("Doctor profile not found.");
      return createAvailability({
        doctor: myDoctor.id,
        weekday,
        start_time: startTime,
        end_time: endTime,
        slot_duration_minutes: slotMinutes,
        is_active: true,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAvailability,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["availability"] }),
    onError: (err) => setError(extractErrorMessage(err)),
  });

  if (doctors.isLoading) return <Spinner />;
  if (!myDoctor) return <ErrorBanner message="No doctor profile found for this account." />;

  return (
    <div className="page-stack">
      <h2 className="page-heading">Availability</h2>
      <p className="muted-text">
        Weekly recurring windows patients and staff can book against. Slots are generated
        automatically within each window at the given duration.
      </p>

      <Card title="Add a weekly window">
        {error && <ErrorBanner message={error} />}
        <div className="field-row">
          <label className="field">
            <span>Day</span>
            <select value={weekday} onChange={(e) => setWeekday(Number(e.target.value))}>
              {WEEKDAYS.map((day, i) => (
                <option key={day} value={i}>
                  {day}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Start time</span>
            <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
          </label>
          <label className="field">
            <span>End time</span>
            <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
          </label>
          <label className="field">
            <span>Slot length (min)</span>
            <input
              type="number"
              min={5}
              step={5}
              value={slotMinutes}
              onChange={(e) => setSlotMinutes(Number(e.target.value))}
            />
          </label>
        </div>
        <button className="btn btn-primary" disabled={createMutation.isPending} onClick={() => createMutation.mutate()}>
          {createMutation.isPending ? "Adding..." : "Add window"}
        </button>
      </Card>

      <Card title="Current schedule">
        {availability.isLoading && <Spinner />}
        {!availability.isLoading && (availability.data ?? []).length === 0 && (
          <EmptyState message="No availability configured yet — patients/staff can't book you until you add a window above." />
        )}
        {availability.data?.map((a) => (
          <div key={a.id} className="list-row list-row-bordered">
            <div className="list-row-title">
              {WEEKDAYS[a.weekday]} &middot; {a.start_time.slice(0, 5)}–{a.end_time.slice(0, 5)} &middot; {a.slot_duration_minutes}
              min slots
            </div>
            <button className="btn btn-ghost btn-danger" disabled={deleteMutation.isPending} onClick={() => deleteMutation.mutate(a.id)}>
              Remove
            </button>
          </div>
        ))}
      </Card>
    </div>
  );
}
