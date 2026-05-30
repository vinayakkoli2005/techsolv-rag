# backend/tests/test_ingest.py
from unittest.mock import patch
from app.ingest import ingest_pair

def test_ingest_pair(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "x")

    yt_meta = {"title": "A", "url": "yt", "views": 1000, "likes": 80, "comments": 20,
               "duration": 60, "upload_date": "20250101", "creator": "c1",
               "followers": 100, "hashtags": [], "engagement_rate": 10.0}
    ig_meta = {"title": None, "url": "ig", "views": 500, "likes": 30, "comments": 5,
               "duration": 30, "upload_date": "2025-01-01", "creator": "c2",
               "followers": 200, "hashtags": [], "engagement_rate": 7.0}

    with patch("app.ingest.fetch_youtube_metadata", return_value=yt_meta), \
         patch("app.ingest.fetch_instagram_metadata", return_value=ig_meta), \
         patch("app.ingest.fetch_youtube_transcript", return_value="yt transcript text " * 50), \
         patch("app.ingest.fetch_instagram_transcript", return_value="ig transcript text " * 50), \
         patch("app.ingest.extract_youtube_id", return_value="abc"):
        result = ingest_pair("https://youtube.com/watch?v=abc", "https://instagram.com/reel/x/")
        assert result["A"]["creator"] == "c1"
        assert result["B"]["creator"] == "c2"
        assert result["A"]["chunks"] > 0
        assert result["B"]["chunks"] > 0
