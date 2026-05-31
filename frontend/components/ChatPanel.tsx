"use client";
import { useState } from "react";
import { streamChat } from "@/lib/api";
import type { ChatMessage, Citation } from "@/lib/types";

export function ChatPanel({ ready }: { ready: boolean }) {
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);

  async function send() {
    if (!input.trim() || streaming) return;
    const q = input.trim();
    setInput("");

    const userMsg: ChatMessage = { role: "user", content: q };
    const assistantMsg: ChatMessage = { role: "assistant", content: "" };
    setMsgs((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    let accumulated = "";

    await streamChat(
      q,
      (token) => {
        accumulated += token;
        const text = accumulated;
        setMsgs((prev) => {
          const next = [...prev];
          next[next.length - 1] = { role: "assistant", content: text };
          return next;
        });
      },
      (citations: Citation[]) => {
        setMsgs((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, citations };
          return next;
        });
      },
      () => setStreaming(false),
      (err) => {
        setStreaming(false);
        setMsgs((prev) => {
          const next = [...prev];
          next[next.length - 1] = { role: "assistant", content: `Error: ${err}` };
          return next;
        });
      },
    );
  }

  const suggestions = [
    "Compare the hooks of both videos",
    "Which video has better engagement and why?",
    "What is the tone and style of each video?",
    "Which creator has a stronger call to action?",
  ]

  return (
    <div className="flex h-[60vh] flex-col rounded-lg border border-zinc-800 bg-zinc-900">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {msgs.length === 0 && (
          <div className="space-y-3">
            <div className="text-sm text-zinc-500">
              {ready
                ? "Ask about the videos, or try one of these:"
                : "Ingest videos to start chatting."}
            </div>
            {ready && (
              <div className="flex flex-wrap gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => setInput(s)}
                    className="rounded-full border border-zinc-700 bg-zinc-800 px-3 py-1 text-xs text-zinc-300 hover:border-emerald-500 hover:text-emerald-300 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user" ? "bg-emerald-500/20 text-white" : "bg-zinc-800 text-zinc-100"
              }`}
            >
              {m.role === "assistant" && !m.content ? (
                <span className="animate-pulse text-zinc-400">Thinking…</span>
              ) : (
                <div className="whitespace-pre-wrap">{m.content}</div>
              )}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {m.citations.map((c, j) => (
                    <span
                      key={j}
                      className="rounded bg-zinc-700 px-1.5 py-0.5 text-[10px] text-zinc-300"
                    >
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
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          className="flex-1 rounded bg-zinc-800 px-3 py-2 text-sm text-white"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={ready ? "Type a question…" : "Ingest videos first"}
          disabled={!ready || streaming}
        />
        <button
          type="submit"
          disabled={!ready || streaming}
          className="rounded bg-emerald-500 px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
        >
          {streaming ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
