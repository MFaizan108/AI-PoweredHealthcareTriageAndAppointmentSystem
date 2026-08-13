import { api } from "./client";

// Lab reports / message attachments are served by authenticated Django views, not a public
// MEDIA_URL path (see docs/security_review.md) — a plain `<a href>` can't carry the JWT bearer
// token, so the file has to be fetched through the same axios instance every other API call
// uses, then handed to the browser as a blob URL.
export async function openAuthenticatedFile(url: string) {
  const response = await api.get(url, { responseType: "blob" });
  const blobUrl = URL.createObjectURL(response.data as Blob);
  window.open(blobUrl, "_blank", "noopener,noreferrer");
  setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
}
