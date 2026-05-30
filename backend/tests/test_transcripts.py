# backend/tests/test_transcripts.py
from unittest.mock import patch, MagicMock
from app.transcripts import fetch_youtube_transcript, extract_youtube_id

def test_extract_youtube_id_standard():
    assert extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

def test_extract_youtube_id_short():
    assert extract_youtube_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

def test_fetch_youtube_transcript_success():
    fake_segments = [
        {"text": "hello", "start": 0.0, "duration": 1.0},
        {"text": "world", "start": 1.0, "duration": 1.0},
    ]
    with patch("app.transcripts.YouTubeTranscriptApi.get_transcript", return_value=fake_segments):
        text = fetch_youtube_transcript("dQw4w9WgXcQ")
        assert "hello" in text and "world" in text

from unittest.mock import patch
from app.transcripts import fetch_instagram_transcript

def test_fetch_instagram_transcript_success(tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake")
    with patch("app.transcripts._download_audio", return_value=str(audio_path)), \
         patch("app.transcripts._whisper_transcribe", return_value="hello reel"):
        text = fetch_instagram_transcript("https://www.instagram.com/reel/ABC123/")
        assert text == "hello reel"
