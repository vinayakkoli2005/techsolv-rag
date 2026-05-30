# backend/tests/test_rag.py
from unittest.mock import patch, MagicMock
from app.rag import build_rag_chain, format_citations
from langchain_core.documents import Document

def test_format_citations():
    docs = [
        Document(page_content="hello", metadata={"video_id": "A", "chunk_index": 0}),
        Document(page_content="world", metadata={"video_id": "B", "chunk_index": 3}),
    ]
    s = format_citations(docs)
    assert "Video A, chunk 0" in s
    assert "Video B, chunk 3" in s

def test_build_rag_chain_returns_callable(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))
    from app.config import Settings
    s = Settings()
    fake_llm = MagicMock()
    with patch("app.rag.get_llm", return_value=fake_llm):
        chain = build_rag_chain(s)
        assert chain is not None
