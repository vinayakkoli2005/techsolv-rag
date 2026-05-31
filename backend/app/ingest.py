# backend/app/ingest.py
import os
import json
from typing import Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .config import settings
from .vectorstore import get_vectorstore, add_chunks, clear_collection
from .transcripts import (
    extract_youtube_id, fetch_youtube_transcript, fetch_instagram_transcript,
)
from .metadata import fetch_youtube_metadata, fetch_instagram_metadata

COLLECTION_NAME = "videos"

def _chunk(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    return splitter.split_text(text)

def _save_metadata(meta: Dict[str, Any]) -> None:
    os.makedirs(settings.data_dir, exist_ok=True)
    with open(os.path.join(settings.data_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

def ingest_pair(youtube_url: str, instagram_url: str) -> Dict[str, Any]:
    vs = get_vectorstore(settings, collection_name=COLLECTION_NAME)
    clear_collection(vs)
    vs = get_vectorstore(settings, collection_name=COLLECTION_NAME)

    yt_id = extract_youtube_id(youtube_url)
    yt_transcript = fetch_youtube_transcript(yt_id)
    yt_meta = fetch_youtube_metadata(youtube_url)
    ig_transcript = fetch_instagram_transcript(instagram_url)
    ig_meta = fetch_instagram_metadata(instagram_url)

    # Fall back to description when transcript unavailable so Video A has some RAG content
    yt_text = yt_transcript or yt_meta.get("description") or ""
    ig_text = ig_transcript or ig_meta.get("description") or ""

    yt_chunks = _chunk(yt_text) if yt_text else []
    ig_chunks = _chunk(ig_text) if ig_text else []

    if yt_chunks:
        add_chunks(
            vs,
            yt_chunks,
            [{"video_id": "A", "chunk_index": i, "source_url": youtube_url}
             for i in range(len(yt_chunks))],
        )
    if ig_chunks:
        add_chunks(
            vs,
            ig_chunks,
            [{"video_id": "B", "chunk_index": i, "source_url": instagram_url}
             for i in range(len(ig_chunks))],
        )

    result = {
        "A": {**yt_meta, "platform": "youtube", "chunks": len(yt_chunks)},
        "B": {**ig_meta, "platform": "instagram", "chunks": len(ig_chunks)},
    }
    _save_metadata(result)
    return result
