# backend/tests/test_metadata.py
from unittest.mock import patch, MagicMock
from app.metadata import fetch_youtube_metadata, fetch_instagram_metadata, compute_engagement_rate

def test_compute_engagement_rate():
    assert compute_engagement_rate(views=1000, likes=80, comments=20) == 10.0
    assert compute_engagement_rate(views=0, likes=0, comments=0) == 0.0

def test_fetch_youtube_metadata():
    fake = {
        "id": "abc",
        "title": "Hook test",
        "view_count": 1000,
        "like_count": 80,
        "comment_count": 20,
        "duration": 60,
        "upload_date": "20250101",
        "channel": "Creator",
        "channel_follower_count": 5000,
        "tags": ["tag1", "tag2"],
        "webpage_url": "https://youtube.com/watch?v=abc",
    }
    with patch("app.metadata._yt_dlp_extract", return_value=fake):
        m = fetch_youtube_metadata("https://youtube.com/watch?v=abc")
        assert m["views"] == 1000
        assert m["engagement_rate"] == 10.0
        assert m["creator"] == "Creator"
        assert m["followers"] == 5000

def test_fetch_instagram_metadata():
    fake_post = MagicMock()
    fake_post.video_view_count = 5000
    fake_post.likes = 400
    fake_post.comments = 100
    fake_post.owner_username = "creator_ig"
    fake_post.caption_hashtags = ["fun", "reel"]
    fake_post.date_utc.isoformat.return_value = "2025-01-01T00:00:00"
    fake_post.video_duration = 30
    fake_post.url = "https://instagram.com/reel/X"

    fake_profile = MagicMock()
    fake_profile.followers = 12000

    with patch("app.metadata._il_post_from_url", return_value=fake_post), \
         patch("app.metadata._il_profile", return_value=fake_profile):
        m = fetch_instagram_metadata("https://www.instagram.com/reel/X/")
        assert m["views"] == 5000
        assert m["likes"] == 400
        assert m["comments"] == 100
        assert m["creator"] == "creator_ig"
        assert m["followers"] == 12000
        assert m["engagement_rate"] == 10.0
