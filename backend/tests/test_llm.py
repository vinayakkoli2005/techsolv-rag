# backend/tests/test_llm.py
from unittest.mock import patch
from app.llm import get_llm

def test_get_llm_groq(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "x")
    from app.config import Settings
    s = Settings()
    llm = get_llm(s)
    assert llm.__class__.__name__ == "ChatGroq"

def test_get_llm_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    from app.config import Settings
    s = Settings()
    llm = get_llm(s)
    assert llm.__class__.__name__ == "ChatOpenAI"

def test_get_llm_missing_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    from app.config import Settings
    s = Settings()
    import pytest
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        get_llm(s)
