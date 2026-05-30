# backend/app/metadata.py
import re
from typing import Dict, Any
import yt_dlp
import instaloader

def compute_engagement_rate(views: int, likes: int, comments: int) -> float:
    if not views:
        return 0.0
    return round((likes + comments) / views * 100, 2)

def _yt_dlp_extract(url: str) -> Dict[str, Any]:
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)

def fetch_youtube_metadata(url: str) -> Dict[str, Any]:
    info = _yt_dlp_extract(url)
    views = info.get("view_count") or 0
    likes = info.get("like_count") or 0
    comments = info.get("comment_count") or 0
    return {
        "title": info.get("title"),
        "url": info.get("webpage_url", url),
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "creator": info.get("channel"),
        "followers": info.get("channel_follower_count"),
        "hashtags": info.get("tags") or [],
        "engagement_rate": compute_engagement_rate(views, likes, comments),
    }

_IG_SHORTCODE_RE = re.compile(r"instagram\.com/(?:reel|p)/([^/?#]+)")

def _il_post_from_url(url: str):
    m = _IG_SHORTCODE_RE.search(url)
    if not m:
        raise ValueError(f"Could not parse Instagram shortcode from {url}")
    L = instaloader.Instaloader(download_pictures=False, download_videos=False,
                                 download_video_thumbnails=False, save_metadata=False)
    return instaloader.Post.from_shortcode(L.context, m.group(1))

def _il_profile(username: str):
    L = instaloader.Instaloader()
    return instaloader.Profile.from_username(L.context, username)

def fetch_instagram_metadata(url: str) -> Dict[str, Any]:
    post = _il_post_from_url(url)
    views = getattr(post, "video_view_count", None) or 0
    likes = post.likes or 0
    comments = post.comments or 0
    try:
        profile = _il_profile(post.owner_username)
        followers = profile.followers
    except Exception:
        followers = None
    return {
        "title": None,
        "url": url,
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration": getattr(post, "video_duration", None),
        "upload_date": post.date_utc.isoformat(),
        "creator": post.owner_username,
        "followers": followers,
        "hashtags": list(post.caption_hashtags or []),
        "engagement_rate": compute_engagement_rate(views, likes, comments),
    }
