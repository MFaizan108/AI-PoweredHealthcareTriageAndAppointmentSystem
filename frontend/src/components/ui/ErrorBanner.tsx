export type BannerTone = "danger" | "success" | "warning" | "info";

const ICON_BY_TONE: Record<BannerTone, string> = {
  danger: "⚠️",
  success: "✅",
  warning: "⚠️",
  info: "ℹ️",
};

export function ErrorBanner({ message, tone = "danger" }: { message: string; tone?: BannerTone }) {
  return (
    <div className={`error-banner${tone !== "danger" ? ` error-banner-${tone}` : ""}`} role="alert">
      <span className="error-banner-icon" aria-hidden="true">
        {ICON_BY_TONE[tone]}
      </span>
      <span>{message}</span>
    </div>
  );
}
