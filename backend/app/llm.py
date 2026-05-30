# backend/app/llm.py
from langchain_core.language_models import BaseChatModel
from .config import Settings

def get_llm(settings: Settings, streaming: bool = True) -> BaseChatModel:
    provider = settings.llm_provider
    if provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model="gemma2-9b-it",
            temperature=0.3,
            streaming=streaming,
        )
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            temperature=0.3,
            streaming=streaming,
        )
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model="claude-3-5-haiku-latest",
            temperature=0.3,
            streaming=streaming,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
