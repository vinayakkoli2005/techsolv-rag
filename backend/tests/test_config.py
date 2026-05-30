# backend/tests/test_config.py
import os
from app.config import Settings

def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    s = Settings()
    assert s.llm_provider == "groq"
    assert s.groq_api_key == "test-key"
    assert s.chroma_mode == "local"

def test_settings_provider_validation(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "invalid")
    import pytest
    with pytest.raises(ValueError):
        Settings()
