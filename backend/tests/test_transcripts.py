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
