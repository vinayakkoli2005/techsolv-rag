# backend/app/schemas.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl

class IngestRequest(BaseModel):
    youtube_url: HttpUrl
    instagram_url: HttpUrl

class VideoMetadata(BaseModel):
    title: Optional[str] = None
    url: str
    platform: str
    views: int
    likes: int
    comments: int
    duration: Optional[float] = None
    upload_date: Optional[str] = None
    creator: Optional[str] = None
    followers: Optional[int] = None
    hashtags: List[str] = []
    engagement_rate: float
    chunks: int

class IngestResponse(BaseModel):
    A: VideoMetadata
    B: VideoMetadata

class ChatRequest(BaseModel):
    question: str
