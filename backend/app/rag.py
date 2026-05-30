# backend/app/rag.py
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from .config import Settings
from .llm import get_llm
from .vectorstore import get_vectorstore

SYSTEM_PROMPT = """You are a creator analytics assistant comparing two short-form videos: Video A (YouTube) and Video B (Instagram Reel).

Use ONLY the provided transcript chunks and metadata to answer. When citing, use the format [Video X, chunk N]. If the answer isn't in the chunks, say you don't know.

Be concise, concrete, and reference specific lines from the transcripts when comparing hooks, pacing, or content."""

_memory = ConversationBufferWindowMemory(k=10, return_messages=True, memory_key="history")

def format_citations(docs: List[Document]) -> str:
    parts = []
    for d in docs:
        vid = d.metadata.get("video_id", "?")
        idx = d.metadata.get("chunk_index", "?")
        parts.append(f"[Video {vid}, chunk {idx}]")
    return " ".join(parts)

def _format_docs(docs: List[Document]) -> str:
    lines = []
    for d in docs:
        vid = d.metadata.get("video_id", "?")
        idx = d.metadata.get("chunk_index", "?")
        lines.append(f"[Video {vid}, chunk {idx}]: {d.page_content}")
    return "\n\n".join(lines)

def build_rag_chain(settings: Settings):
    vs = get_vectorstore(settings, collection_name="videos")
    retriever = vs.as_retriever(search_kwargs={"k": 6})
    llm = get_llm(settings, streaming=True)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])

    def _get_history(_):
        return _memory.load_memory_variables({})["history"]

    chain = (
        {
            "context": (lambda x: x["question"]) | retriever | RunnableLambda(_format_docs),
            "question": lambda x: x["question"],
            "history": RunnableLambda(_get_history),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever, _memory
