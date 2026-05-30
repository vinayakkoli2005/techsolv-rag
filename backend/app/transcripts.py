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

import os
import tempfile
import yt_dlp

_whisper_model = None

def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model

def _download_audio(url: str, out_dir: str) -> str:
    out_template = os.path.join(out_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id")
    return os.path.join(out_dir, f"{video_id}.mp3")

def _whisper_transcribe(audio_path: str) -> str:
    model = _get_whisper_model()
    segments, _ = model.transcribe(audio_path, beam_size=1)
    return " ".join(seg.text for seg in segments).strip()

def fetch_instagram_transcript(url: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        audio = _download_audio(url, tmp)
        return _whisper_transcribe(audio)
