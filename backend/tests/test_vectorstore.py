# backend/tests/test_vectorstore.py
from app.vectorstore import get_vectorstore, add_chunks

def test_add_and_retrieve_chunks(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.setenv("CHROMA_MODE", "local")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "x")
    from app.config import Settings
    s = Settings()
    vs = get_vectorstore(s, collection_name="test_col")
    add_chunks(vs, ["The hook in the first 5 seconds was a question"], [{"video_id": "A", "chunk_index": 0}])
    results = vs.similarity_search("hook", k=1)
    assert len(results) == 1
    assert results[0].metadata["video_id"] == "A"
