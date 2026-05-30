import type { IngestResponse, Citation } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function ingestVideos(youtube_url: string, instagram_url: string): Promise<IngestResponse> {
  const r = await fetch(`${BASE}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ youtube_url, instagram_url }),
  });
  if (!r.ok) throw new Error(`Ingest failed: ${r.status}`);
  return r.json();
}

export async function streamChat(
  question: string,
  onToken: (t: string) => void,
  onCitations: (c: Citation[]) => void,
  onDone: () => void,
  onError: (msg: string) => void,
) {
  const r = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!r.body) { onError("No response body"); return; }

  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const block of events) {
      const lines = block.split("\n");
      let event = "message", data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data = line.slice(5).trim();
      }
      if (!data) continue;
      try {
        const parsed = JSON.parse(data);
        if (event === "token") onToken(parsed.text);
        else if (event === "citations") onCitations(parsed.citations);
        else if (event === "done") onDone();
        else if (event === "error") onError(parsed.error);
      } catch {}
    }
  }
}
