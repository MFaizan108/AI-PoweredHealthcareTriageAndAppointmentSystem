import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { getTriageAssessment, listEmergencyGuidance, listTriageAssessments, submitTriageAssessment } from "../../api/triage";
import type { TriageAssessment } from "../../api/types";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

function AISummaryBlock({ assessmentId, initial }: { assessmentId: number; initial: TriageAssessment }) {
  const { data } = useQuery({
    queryKey: ["triage-assessment", assessmentId],
    queryFn: () => getTriageAssessment(assessmentId),
    initialData: initial,
    refetchInterval: (query) => (query.state.data?.ai_summary_status === "pending" ? 2000 : false),
  });

  if (!data || data.ai_summary_status === "not_requested") return null;

  return (
    <div className="ai-summary-block">
      <h3 className="card-subtitle">AI-generated explanation</h3>
      {data.ai_summary_status === "pending" && (
        <div className="muted-text pending-row">
          <Spinner size={16} /> Generating a plain-language summary...
        </div>
      )}
      {data.ai_summary_status === "ready" && <p>{data.ai_summary}</p>}
      {data.ai_summary_status === "failed" && (
        <p className="muted-text">The AI summary couldn't be generated ({data.ai_summary_error || "unknown error"}). The result above is still valid.</p>
      )}
    </div>
  );
}

function AssessmentResult({ assessment }: { assessment: TriageAssessment }) {
  const guidance = useQuery({ queryKey: ["emergency-guidance"], queryFn: listEmergencyGuidance });
  const matchedGuidance = guidance.data?.find((g) => g.urgency === assessment.urgency);
  const showGuidance = assessment.urgency === "high" || assessment.urgency === "emergency";

  return (
    <Card
      title={
        <>
          Result: <StatusBadge status={assessment.urgency} />
        </>
      }
    >
      <p className="disclaimer-text">{assessment.disclaimer}</p>

      {assessment.suggested_department_detail && (
        <p>
          Suggested department: <strong>{assessment.suggested_department_detail.name}</strong>
        </p>
      )}
      {assessment.reasoning && <p className="muted-text">{assessment.reasoning}</p>}

      {assessment.detected_symptoms.length > 0 && (
        <div className="chip-row">
          {assessment.detected_symptoms.map((s) => (
            <span key={s.id} className="chip">
              {s.name}
            </span>
          ))}
        </div>
      )}

      <AISummaryBlock assessmentId={assessment.id} initial={assessment} />

      {showGuidance && matchedGuidance && (
        <div className="emergency-guidance">
          <h3 className="card-subtitle">{matchedGuidance.title}</h3>
          <p>{matchedGuidance.content}</p>
          {matchedGuidance.emergency_numbers && <p><strong>Emergency numbers:</strong> {matchedGuidance.emergency_numbers}</p>}
        </div>
      )}
    </Card>
  );
}

export function TriagePage() {
  const queryClient = useQueryClient();
  const [symptomsText, setSymptomsText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TriageAssessment | null>(null);

  const history = useQuery({ queryKey: ["triage-history"], queryFn: () => listTriageAssessments() });

  const submitMutation = useMutation({
    mutationFn: () => submitTriageAssessment({ symptoms_text: symptomsText, use_ai_summary: true }),
    onSuccess: (data) => {
      setResult(data);
      setSymptomsText("");
      queryClient.invalidateQueries({ queryKey: ["triage-history"] });
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="page-stack">
      <h2 className="page-heading">AI Symptom Triage</h2>

      <Card title="Describe your symptoms">
        {error && <ErrorBanner message={error} />}
        <textarea
          value={symptomsText}
          onChange={(e) => setSymptomsText(e.target.value)}
          rows={4}
          placeholder="e.g. I have had a fever and cough for 3 days, and my chest feels tight..."
        />
        <button
          className="btn btn-primary"
          disabled={!symptomsText.trim() || submitMutation.isPending}
          onClick={() => {
            setError(null);
            submitMutation.mutate();
          }}
        >
          {submitMutation.isPending ? "Analyzing..." : "Get triage assessment"}
        </button>
      </Card>

      {result && <AssessmentResult assessment={result} />}

      <Card title="Past assessments">
        {history.isLoading && <Spinner />}
        {!history.isLoading && (history.data ?? []).length === 0 && <EmptyState message="No previous assessments." />}
        {history.data?.map((a) => (
          <div key={a.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">{a.symptoms_text.slice(0, 80)}{a.symptoms_text.length > 80 ? "..." : ""}</div>
              <div className="list-row-subtitle">{formatDateTime(a.created_at)}</div>
            </div>
            <StatusBadge status={a.urgency} />
          </div>
        ))}
      </Card>
    </div>
  );
}
