"use client";
import { useState } from "react";

export function UrlForm({ onSubmit, disabled }: { onSubmit: (yt: string, ig: string) => void; disabled: boolean }) {
  const [yt, setYt] = useState("");
  const [ig, setIg] = useState("");
  return (
    <form
      className="flex flex-col gap-2 md:flex-row md:items-end"
      onSubmit={(e) => { e.preventDefault(); onSubmit(yt, ig); }}
    >
      <label className="flex-1">
        <span className="block text-xs text-zinc-400">YouTube URL</span>
        <input className="w-full rounded bg-zinc-800 px-3 py-2 text-sm"
          value={yt} onChange={(e) => setYt(e.target.value)}
          placeholder="https://youtube.com/watch?v=..." required />
      </label>
      <label className="flex-1">
        <span className="block text-xs text-zinc-400">Instagram Reel URL</span>
        <input className="w-full rounded bg-zinc-800 px-3 py-2 text-sm"
          value={ig} onChange={(e) => setIg(e.target.value)}
          placeholder="https://instagram.com/reel/..." required />
      </label>
      <button className="rounded bg-emerald-500 px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
        type="submit" disabled={disabled}>
        {disabled ? "Ingesting…" : "Compare"}
      </button>
    </form>
  );
}
