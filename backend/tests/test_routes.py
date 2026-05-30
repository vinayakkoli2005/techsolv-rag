# backend/tests/test_routes.py
from unittest.mock import patch
from fastapi.testclient import TestClient

def test_health(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "x")
    from app.main import app
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_ingest_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    fake_result = {
        "A": {"title": "A", "url": "yt", "platform": "youtube", "views": 1000, "likes": 80,
              "comments": 20, "duration": 60, "upload_date": "20250101", "creator": "c1",
              "followers": 100, "hashtags": [], "engagement_rate": 10.0, "chunks": 5},
        "B": {"title": None, "url": "ig", "platform": "instagram", "views": 500, "likes": 30,
              "comments": 5, "duration": 30, "upload_date": "2025-01-01", "creator": "c2",
              "followers": 200, "hashtags": [], "engagement_rate": 7.0, "chunks": 3},
    }
    with patch("app.routes.ingest_pair", return_value=fake_result):
        from app.main import app
        client = TestClient(app)
        r = client.post("/api/ingest", json={
            "youtube_url": "https://youtube.com/watch?v=abc",
            "instagram_url": "https://instagram.com/reel/x/",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["A"]["creator"] == "c1"
        assert body["B"]["creator"] == "c2"
