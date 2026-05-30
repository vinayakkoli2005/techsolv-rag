"use client";
import { useRef, useState } from "react";
import { streamChat } from "@/lib/api";
import type { ChatMessage, Citation } from "@/lib/types";

export function ChatPanel({ ready }: { ready: boolean }) {
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const assistantRef = useRef<string>("");

  async function send() {
    if (!input.trim() || streaming) return;
    const q = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: q }, { role: "assistant", content: "" }]);
    setStreaming(true);
    assistantRef.current = "";

    await streamChat(
      q,
      (token) => {
        assistantRef.current += token;
        setMsgs((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { role: "assistant", content: assistantRef.current };
          return copy;
        });
      },
      (citations: Citation[]) => {
        setMsgs((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { ...copy[copy.length - 1], citations };
          return copy;
        });
      },
      () => setStreaming(false),
      (err) => {
        setStreaming(false);
        setMsgs((m) => [...m, { role: "assistant", content: `Error: ${err}` }]);
      },
    );
  }

  return (
    <div className="flex h-[60vh] flex-col rounded-lg border border-zinc-800 bg-zinc-900">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {msgs.length === 0 && (
          <div className="text-sm text-zinc-500">
            {ready ? "Ask about the videos — e.g. 'Compare the hooks in the first 5 seconds.'" : "Ingest videos to start chatting."}
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "bg-emerald-500/20" : "bg-zinc-800"}`}>
              <div className="whitespace-pre-wrap">{m.content}</div>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {m.citations.map((c, j) => (
                    <span key={j} className="rounded bg-zinc-700 px-1.5 py-0.5 text-[10px] text-zinc-300">
                      Video {c.video_id} · chunk {c.chunk_index}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <form
        className="flex gap-2 border-t border-zinc-800 p-3"
        onSubmit={(e) => { e.preventDefault(); send(); }}
      >
        <input
          className="flex-1 rounded bg-zinc-800 px-3 py-2 text-sm"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={ready ? "Type a question…" : "Ingest videos first"}
          disabled={!ready || streaming}
        />
        <button type="submit" disabled={!ready || streaming}
          className="rounded bg-emerald-500 px-4 py-2 text-sm font-medium text-black disabled:opacity-50">
          Send
        </button>
      </form>
    </div>
  );
}
