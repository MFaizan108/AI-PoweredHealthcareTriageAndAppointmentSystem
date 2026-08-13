import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { getAIProviderSettings, updateAIProviderSettings, type UpdateAIProviderSettingsPayload } from "../../api/triage";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";

export function AdminSettingsPage() {
  const queryClient = useQueryClient();
  const settings = useQuery({ queryKey: ["ai-provider-settings"], queryFn: getAIProviderSettings });
  const [form, setForm] = useState<UpdateAIProviderSettingsPayload | null>(null);
  const [groqApiKey, setGroqApiKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings.data && !form) {
      setForm({
        is_enabled: settings.data.is_enabled,
        provider: settings.data.provider,
        ollama_base_url: settings.data.ollama_base_url,
        ollama_model: settings.data.ollama_model,
        groq_model: settings.data.groq_model,
        timeout_seconds: settings.data.timeout_seconds,
      });
    }
  }, [settings.data, form]);

  const saveMutation = useMutation({
    mutationFn: () => updateAIProviderSettings({ ...form, ...(groqApiKey ? { groq_api_key: groqApiKey } : {}) }),
    onSuccess: (data) => {
      queryClient.setQueryData(["ai-provider-settings"], data);
      setGroqApiKey("");
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  if (settings.isLoading || !form) return <Spinner />;
  if (settings.isError || !settings.data) return <ErrorBanner message="Could not load AI provider settings." />;

  return (
    <div className="page-stack">
      <h2 className="page-heading">System Settings</h2>

      <Card title="AI Provider (Triage Layer 3 summary)">
        {error && <ErrorBanner message={error} />}
        {saved && <ErrorBanner tone="success" message="Saved." />}

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={form.is_enabled ?? false}
            onChange={(e) => setForm((f) => ({ ...f, is_enabled: e.target.checked }))}
          />
          Enable AI summary (rule-based triage always runs regardless)
        </label>

        <label className="field">
          <span>Provider</span>
          <select value={form.provider} onChange={(e) => setForm((f) => ({ ...f, provider: e.target.value as "ollama" | "groq" }))}>
            <option value="ollama">Ollama (local)</option>
            <option value="groq">Groq (cloud)</option>
          </select>
        </label>

        {form.provider === "ollama" ? (
          <div className="field-row">
            <label className="field">
              <span>Ollama base URL</span>
              <input type="text" value={form.ollama_base_url} onChange={(e) => setForm((f) => ({ ...f, ollama_base_url: e.target.value }))} />
            </label>
            <label className="field">
              <span>Ollama model</span>
              <input type="text" value={form.ollama_model} onChange={(e) => setForm((f) => ({ ...f, ollama_model: e.target.value }))} />
            </label>
          </div>
        ) : (
          <div className="field-row">
            <label className="field">
              <span>Groq model</span>
              <input type="text" value={form.groq_model} onChange={(e) => setForm((f) => ({ ...f, groq_model: e.target.value }))} />
            </label>
            <label className="field">
              <span>Groq API key {settings.data.groq_api_key_set ? "(set — leave blank to keep)" : "(not set)"}</span>
              <input type="password" value={groqApiKey} onChange={(e) => setGroqApiKey(e.target.value)} />
            </label>
          </div>
        )}

        <label className="field">
          <span>Timeout (seconds)</span>
          <input
            type="number"
            min={1}
            value={form.timeout_seconds}
            onChange={(e) => setForm((f) => ({ ...f, timeout_seconds: Number(e.target.value) }))}
          />
        </label>

        <button className="btn btn-primary" disabled={saveMutation.isPending} onClick={() => saveMutation.mutate()}>
          {saveMutation.isPending ? "Saving..." : "Save settings"}
        </button>
      </Card>
    </div>
  );
}
