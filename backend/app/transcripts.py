# backend/app/transcripts.py
import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi

YOUTUBE_ID_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})")

def extract_youtube_id(url: str) -> str:
    m = YOUTUBE_ID_RE.search(url)
    if not m:
        raise ValueError(f"Could not extract YouTube video ID from: {url}")
    return m.group(1)

def fetch_youtube_transcript(video_id: str) -> str:
    segments = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join(s["text"] for s in segments).strip()
