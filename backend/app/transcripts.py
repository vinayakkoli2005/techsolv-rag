# backend/app/transcripts.py
import re
import os
import glob as _glob
import tempfile
import sys
import traceback
import json
import urllib.request
import http.cookiejar
from typing import Optional
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

YOUTUBE_ID_RE = re.compile(r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})")

_COOKIES_FILE = os.path.join(os.path.dirname(__file__), "..", "www.instagram.com_cookies.txt")
_YT_COOKIES_FILE = os.path.join(os.path.dirname(__file__), "..", "yt_auth_cookies.txt")

_FFMPEG_LOCATIONS = [
    r"C:\Users\vinay\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin",
    r"C:\ProgramData\chocolatey\bin",
    r"C:\ffmpeg\bin",
]

def _find_ffmpeg_location() -> str | None:
    for loc in _FFMPEG_LOCATIONS:
        if os.path.exists(os.path.join(loc, "ffmpeg.exe")):
            return loc
    return None

def extract_youtube_id(url: str) -> str:
    m = YOUTUBE_ID_RE.search(url)
    if not m:
        raise ValueError(f"Could not extract YouTube video ID from: {url}")
    return m.group(1)

def fetch_youtube_transcript(video_id: str) -> str:
    print(f"[yt_transcript] fetching for video_id={video_id}", file=sys.stderr, flush=True)
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except Exception:
        print(f"[yt_transcript] list_transcripts FAILED:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
        return ""

    # 1. Try manually created English
    try:
        text = " ".join(s["text"] for s in transcript_list.find_manually_created_transcript(["en"]).fetch()).strip()
        print(f"[yt_transcript] tier1 manual EN: {len(text)} chars", file=sys.stderr, flush=True)
        return text
    except Exception as e:
        print(f"[yt_transcript] tier1 failed: {e}", file=sys.stderr, flush=True)

    # 2. Try auto-generated English
    try:
        text = " ".join(s["text"] for s in transcript_list.find_generated_transcript(["en"]).fetch()).strip()
        print(f"[yt_transcript] tier2 auto EN: {len(text)} chars", file=sys.stderr, flush=True)
        return text
    except Exception as e:
        print(f"[yt_transcript] tier2 failed: {e}", file=sys.stderr, flush=True)

    # 3. Take whatever language exists and translate to English
    try:
        available = list(transcript_list)
        print(f"[yt_transcript] available langs: {[t.language_code for t in available]}", file=sys.stderr, flush=True)
        if available:
            translated = available[0].translate("en")
            text = " ".join(s["text"] for s in translated.fetch()).strip()
            print(f"[yt_transcript] tier3 translated: {len(text)} chars", file=sys.stderr, flush=True)
            return text
    except Exception as e:
        print(f"[yt_transcript] tier3 failed: {e}", file=sys.stderr, flush=True)

    # 4. Fetch in native language (no translation)
    try:
        available = list(transcript_list)
        if available:
            text = " ".join(s["text"] for s in available[0].fetch()).strip()
            print(f"[yt_transcript] tier4 native: {len(text)} chars", file=sys.stderr, flush=True)
            return text
    except Exception as e:
        print(f"[yt_transcript] tier4 failed: {e}", file=sys.stderr, flush=True)

    # 5. Fetch subtitle URL directly from yt-dlp info dict (avoids the 429-prone downloader path)
    print(f"[yt_transcript] trying tier5 direct subtitle URL", file=sys.stderr, flush=True)
    text = _fetch_youtube_transcript_direct(video_id)
    if text:
        print(f"[yt_transcript] tier5 direct: {len(text)} chars", file=sys.stderr, flush=True)
        return text

    # 6. yt-dlp subtitle download with cookies (last resort)
    print(f"[yt_transcript] trying tier6 yt-dlp subtitles", file=sys.stderr, flush=True)
    text = _fetch_youtube_transcript_ytdlp(video_id)
    if text:
        print(f"[yt_transcript] tier6 yt-dlp: {len(text)} chars", file=sys.stderr, flush=True)
        return text

    print(f"[yt_transcript] all tiers failed, returning empty", file=sys.stderr, flush=True)
    return ""


def _fetch_youtube_transcript_direct(video_id: str) -> str:
    """Extract subtitle URLs from yt-dlp info dict and fetch them directly via urllib,
    bypassing yt-dlp's downloader which raises on 429."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cookies_file = _YT_COOKIES_FILE if os.path.exists(_YT_COOKIES_FILE) else None
    opts: dict = {"quiet": True, "no_warnings": True, "skip_download": True}
    if cookies_file:
        opts["cookiefile"] = cookies_file

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"[yt_transcript] tier5 extract_info failed: {e}", file=sys.stderr, flush=True)
        return ""

    subs = info.get("subtitles", {})
    auto = info.get("automatic_captions", {})

    # Build a short candidate list: real subtitle langs + only "en" from auto-captions.
    # Do NOT iterate all 100+ translation langs in auto — they all hit the same 429 endpoint.
    candidates: list[tuple[str, list]] = []
    for lang in ("en", *[k for k in subs if k != "en"]):
        if subs.get(lang):
            candidates.append((lang, subs[lang]))
    if auto.get("en"):
        candidates.append(("en-auto", auto["en"]))

    opener = urllib.request.build_opener()
    if cookies_file:
        cj = http.cookiejar.MozillaCookieJar(cookies_file)
        try:
            cj.load(ignore_discard=True, ignore_expires=True)
        except Exception:
            pass
        opener.add_handler(urllib.request.HTTPCookieProcessor(cj))

    for lang, formats in candidates:
        for preferred_ext in ("vtt", "json3", "srv1", "srv2", "ttml"):
            for fmt in formats:
                if fmt.get("ext") != preferred_ext or not fmt.get("url"):
                    continue
                sub_url = fmt["url"]
                print(f"[yt_transcript] tier5 fetching {lang}/{preferred_ext}: {sub_url[:60]}...", file=sys.stderr, flush=True)
                try:
                    req = urllib.request.Request(sub_url, headers={"User-Agent": "Mozilla/5.0"})
                    with opener.open(req, timeout=15) as resp:
                        raw = resp.read().decode("utf-8", errors="ignore")
                    if preferred_ext == "json3":
                        data = json.loads(raw)
                        text = " ".join(
                            e.get("utf8", "") or "".join(s.get("utf8", "") for s in e.get("segs", []))
                            for e in data.get("events", [])
                            if e.get("utf8") or e.get("segs")
                        )
                    else:
                        text = re.sub(r"<[^>]+>", " ", raw)
                    text = re.sub(r"\s+", " ", text).strip()
                    if text:
                        return text
                except Exception as fetch_err:
                    err_str = str(fetch_err)
                    print(f"[yt_transcript] tier5 fetch failed: {err_str}", file=sys.stderr, flush=True)
                    if "429" in err_str:
                        print("[yt_transcript] tier5 rate-limited, aborting", file=sys.stderr, flush=True)
                        return ""
    return ""


def _fetch_youtube_transcript_ytdlp(video_id: str) -> str:
    url = f"https://www.youtube.com/watch?v={video_id}"
    cookies_file = _YT_COOKIES_FILE if os.path.exists(_YT_COOKIES_FILE) else None
    ffmpeg_loc = _find_ffmpeg_location()

    base_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", "hi"],
        "quiet": True,
        "no_warnings": True,
    }
    if ffmpeg_loc:
        base_opts["ffmpeg_location"] = ffmpeg_loc

    # Browser cookie extraction (cookiesfrombrowser) fails on Windows when the backend
    # process can't access the browser's DPAPI keystore. Skip it — use file only.
    cookie_attempts: list = []
    if cookies_file:
        cookie_attempts.append({"cookiefile": cookies_file})
    cookie_attempts.append({})

    for cookie_opt in cookie_attempts:
        print(f"[yt_transcript] tier5 trying {cookie_opt}", file=sys.stderr, flush=True)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                ydl_opts = {**base_opts, "outtmpl": os.path.join(tmp, "%(id)s"), **cookie_opt}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                sub_files = (_glob.glob(os.path.join(tmp, "*.ttml")) +
                             _glob.glob(os.path.join(tmp, "*.vtt")) +
                             _glob.glob(os.path.join(tmp, "*.srt")))
                print(f"[yt_transcript] tier5 sub files: {sub_files}", file=sys.stderr, flush=True)
                if not sub_files:
                    continue
                with open(sub_files[0], encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                text = re.sub(r"<[^>]+>", " ", raw)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    return text
        except Exception:
            print(f"[yt_transcript] tier5 attempt failed:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
    return ""


_whisper_model = None

def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model

def _whisper_transcribe(audio_path: str) -> str:
    model = _get_whisper_model()
    segments, _ = model.transcribe(audio_path, beam_size=1)
    return " ".join(seg.text for seg in segments).strip()

def fetch_instagram_transcript(url: str) -> str:
    # On cloud (no local ffmpeg), skip Whisper — use caption from yt-dlp description instead.
    # Whisper loads a ~150MB model into RAM which OOM-kills Railway's container.
    ffmpeg_loc = _find_ffmpeg_location()
    if not ffmpeg_loc:
        print("[instagram] no local ffmpeg, skipping Whisper — using yt-dlp description as transcript", file=sys.stderr, flush=True)
        return _fetch_instagram_caption_via_ytdlp(url)

    cookies_file = _COOKIES_FILE if os.path.exists(_COOKIES_FILE) else None
    print(f"[instagram] cookies_file={cookies_file!r}  ffmpeg_loc={ffmpeg_loc!r}", file=sys.stderr, flush=True)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
                "quiet": False,
                "no_warnings": False,
            }
            if cookies_file:
                ydl_opts["cookiefile"] = cookies_file
            ydl_opts["ffmpeg_location"] = ffmpeg_loc
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio = os.path.join(tmp, f"{info.get('id')}.mp3")
            print(f"[instagram] audio path: {audio}  exists: {os.path.exists(audio)}", file=sys.stderr, flush=True)
            text = _whisper_transcribe(audio)
            print(f"[instagram] transcript length: {len(text)}", file=sys.stderr, flush=True)
            return text
    except Exception:
        print(f"[instagram] FAILED:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
        return ""


def _fetch_instagram_caption_via_ytdlp(url: str) -> str:
    cookies_file = _COOKIES_FILE if os.path.exists(_COOKIES_FILE) else None
    opts: dict = {"quiet": True, "no_warnings": True, "skip_download": True}
    if cookies_file:
        opts["cookiefile"] = cookies_file
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        text = info.get("description") or info.get("title") or ""
        print(f"[instagram] caption fallback: {len(text)} chars", file=sys.stderr, flush=True)
        return text
    except Exception:
        print(f"[instagram] caption fallback FAILED:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
        return ""
