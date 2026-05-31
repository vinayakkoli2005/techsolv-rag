"use client";
import { MetadataBadge } from "./MetadataBadge";
import type { VideoMeta } from "@/lib/types";

function youtubeEmbed(url: string): string | null {
  const m = url.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  return m ? `https://www.youtube.com/embed/${m[1]}` : null;
}

export function VideoCard({ label, meta }: { label: "A" | "B"; meta: VideoMeta | null }) {
  if (!meta) {
    return <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4 text-sm text-zinc-500">
      Video {label}: not loaded
    </div>;
  }
  const embed = meta.platform === "youtube" ? youtubeEmbed(meta.url) : null;
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Video {label} · {meta.platform}</h3>
        <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-300">
          {meta.engagement_rate > 0 ? `ER ${meta.engagement_rate}%` : "ER –"}
        </span>
      </div>
      {embed ? (
        <iframe className="mb-3 aspect-video w-full rounded" src={embed} allowFullScreen />
      ) : (
        <a className="mb-3 block text-xs text-emerald-300 underline" href={meta.url} target="_blank">
          Open on {meta.platform}
        </a>
      )}
      <div className="grid grid-cols-3 gap-2">
        <MetadataBadge label="Views" value={meta.views > 0 ? meta.views.toLocaleString() : "–"} />
        <MetadataBadge label="Likes" value={meta.likes > 0 ? meta.likes.toLocaleString() : "–"} />
        <MetadataBadge label="Comments" value={meta.comments > 0 ? meta.comments.toLocaleString() : "–"} />
        <MetadataBadge label="Creator" value={meta.creator} />
        <MetadataBadge label="Followers" value={meta.followers?.toLocaleString() ?? null} />
        <MetadataBadge label="Duration" value={meta.duration ? `${Math.round(meta.duration)}s` : null} />
      </div>
    </div>
  );
}
