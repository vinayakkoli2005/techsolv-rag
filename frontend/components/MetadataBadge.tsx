"use client";
export function MetadataBadge({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="flex flex-col items-start rounded-md bg-zinc-800 px-3 py-1.5 text-xs">
      <span className="text-zinc-400">{label}</span>
      <span className="font-mono text-zinc-100">{value ?? "—"}</span>
    </div>
  );
}
