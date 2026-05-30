# backend/app/vectorstore.py
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from .config import Settings

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings

def get_vectorstore(settings: Settings, collection_name: str = "videos") -> Chroma:
    persist_dir = settings.chroma_persist_dir if settings.chroma_mode == "local" else None
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=persist_dir,
    )

def add_chunks(vs: Chroma, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
    vs.add_texts(texts=texts, metadatas=metadatas)

def clear_collection(vs: Chroma) -> None:
    try:
        vs.delete_collection()
    except Exception:
        pass
