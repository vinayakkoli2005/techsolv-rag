export type VideoMeta = {
  title: string | null;
  url: string;
  platform: "youtube" | "instagram";
  views: number;
  likes: number;
  comments: number;
  duration: number | null;
  upload_date: string | null;
  creator: string | null;
  followers: number | null;
  hashtags: string[];
  engagement_rate: number;
  chunks: number;
};

export type IngestResponse = { A: VideoMeta; B: VideoMeta };

export type Citation = { video_id: "A" | "B"; chunk_index: number };

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};
