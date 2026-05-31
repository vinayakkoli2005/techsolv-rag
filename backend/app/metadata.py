# backend/app/metadata.py
import re
import os
import sys
import traceback
import time
import requests
from typing import Dict, Any
import yt_dlp
import instaloader
from .config import settings

_COOKIES_FILE = os.path.join(os.path.dirname(__file__), "..", "www.instagram.com_cookies.txt")

def compute_engagement_rate(views: int, likes: int, comments: int, followers: int | None = None) -> float:
    if views:
        return round((likes + comments) / views * 100, 2)
    if followers:
        return round((likes + comments) / followers * 100, 2)
    return 0.0

_YT_AUTH_COOKIES = os.path.join(os.path.dirname(__file__), "..", "yt_auth_cookies.txt")

def _yt_dlp_extract(url: str, cookiefile: str | None = None) -> Dict[str, Any]:
    opts: Dict[str, Any] = {"quiet": True, "no_warnings": True, "skip_download": True}
    if cookiefile and os.path.exists(cookiefile):
        opts["cookiefile"] = cookiefile
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

def _make_yt_meta(info: Dict[str, Any], url: str) -> Dict[str, Any]:
    views = info.get("view_count") or 0
    likes = info.get("like_count") or 0
    comments = info.get("comment_count") or 0
    print(f"[yt_meta] views={views} likes={likes} comments={comments}", file=sys.stderr, flush=True)
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
        "description": info.get("description") or "",
    }

def fetch_youtube_metadata(url: str) -> Dict[str, Any]:
    for cookiefile in [_YT_AUTH_COOKIES, None]:
        try:
            info = _yt_dlp_extract(url, cookiefile=cookiefile)
            return _make_yt_meta(info, url)
        except Exception:
            print(f"[yt_meta] attempt cookies={cookiefile} failed: {traceback.format_exc()}", file=sys.stderr, flush=True)
    return {
        "title": None,
        "url": url,
        "views": 0,
        "likes": 0,
        "comments": 0,
        "duration": None,
        "upload_date": None,
        "creator": "unknown",
        "followers": None,
        "hashtags": [],
        "engagement_rate": 0.0,
        "description": "",
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

def _fetch_instagram_via_ytdlp(url: str) -> Dict[str, Any]:
    cookies = _COOKIES_FILE if os.path.exists(_COOKIES_FILE) else None
    opts: Dict[str, Any] = {"quiet": True, "no_warnings": True, "skip_download": True}
    if cookies:
        opts["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    views = info.get("view_count") or 0
    likes = info.get("like_count") or 0
    comments = info.get("comment_count") or 0
    followers = info.get("channel_follower_count") or None
    return {
        "title": info.get("title"),
        "url": url,
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "creator": info.get("uploader") or info.get("channel") or "unknown",
        "followers": followers,
        "hashtags": info.get("tags") or [],
        "engagement_rate": compute_engagement_rate(views, likes, comments, followers),
        "description": info.get("description") or "",
    }

def _fetch_instagram_via_apify(url: str) -> Dict[str, Any] | None:
    token = (settings.apify_api_token or "").strip()
    if not token:
        return None
    print(f"[ig_apify] running instagram-scraper for {url}", file=sys.stderr, flush=True)
    run_url = "https://api.apify.com/v2/acts/apify~instagram-scraper/runs"
    payload = {"directUrls": [url], "resultsType": "posts", "resultsLimit": 1}
    try:
        r = requests.post(run_url, json=payload,
                          headers={"Authorization": f"Bearer {token}"}, timeout=15)
        r.raise_for_status()
        run_id = r.json()["data"]["id"]
        dataset_id = r.json()["data"]["defaultDatasetId"]
    except Exception as e:
        print(f"[ig_apify] failed to start run: {e}", file=sys.stderr, flush=True)
        return None

    # Poll for completion (max 90s)
    status_url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs/{run_id}"
    for _ in range(18):
        time.sleep(5)
        try:
            s = requests.get(status_url,
                             headers={"Authorization": f"Bearer {token}"}, timeout=10)
            status = s.json()["data"]["status"]
            print(f"[ig_apify] run status: {status}", file=sys.stderr, flush=True)
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break
        except Exception:
            pass

    # Fetch dataset
    try:
        d = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items?limit=1",
            headers={"Authorization": f"Bearer {token}"}, timeout=10)
        items = d.json()
        if not items:
            print("[ig_apify] empty dataset", file=sys.stderr, flush=True)
            return None
        item = items[0]
        print(f"[ig_apify] raw item keys: {list(item.keys())}", file=sys.stderr, flush=True)
        # Log engagement-related fields explicitly for debugging
        for k in ("videoViewCount","viewsCount","videoPlayCount","playCount","likesCount","likes","videoLikesCount","commentsCount","comments","ownerFollowersCount","followersCount"):
            if k in item:
                print(f"[ig_apify]   {k}={item[k]}", file=sys.stderr, flush=True)
        views = (item.get("videoViewCount") or item.get("viewsCount")
                 or item.get("videoPlayCount") or item.get("playCount") or 0)
        likes = (item.get("likesCount") or item.get("likes")
                 or item.get("videoLikesCount") or 0)
        comments = (item.get("commentsCount") or item.get("comments")
                    or item.get("videoCommentCount") or 0)
        followers = (item.get("ownerFollowersCount") or item.get("followersCount")
                     or item.get("owner", {}).get("followersCount") or None)
        return {
            "title": item.get("caption", "")[:80] if item.get("caption") else None,
            "url": url,
            "views": views,
            "likes": likes,
            "comments": comments,
            "duration": item.get("videoDuration"),
            "upload_date": item.get("timestamp", "")[:10].replace("-", "") if item.get("timestamp") else None,
            "creator": item.get("ownerUsername") or "unknown",
            "followers": followers,
            "hashtags": item.get("hashtags") or [],
            "engagement_rate": compute_engagement_rate(views, likes, comments, followers),
            "description": item.get("caption") or "",
        }
    except Exception as e:
        print(f"[ig_apify] dataset fetch failed: {e}", file=sys.stderr, flush=True)
        return None


def fetch_instagram_metadata(url: str) -> Dict[str, Any]:
    # Apify gives full metrics (views, likes, comments, followers) by scraping the web UI.
    # Falls back to instaloader → yt-dlp → stub when token not set or run fails.
    apify_result = _fetch_instagram_via_apify(url)
    if apify_result:
        return apify_result

    try:
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
            "engagement_rate": compute_engagement_rate(views, likes, comments, followers),
            "description": post.caption or "",
        }
    except Exception:
        pass

    try:
        return _fetch_instagram_via_ytdlp(url)
    except Exception:
        pass

    return {
        "title": None,
        "url": url,
        "views": 0,
        "likes": 0,
        "comments": 0,
        "duration": None,
        "upload_date": None,
        "creator": "unknown",
        "followers": None,
        "hashtags": [],
        "engagement_rate": 0.0,
        "description": "",
    }
