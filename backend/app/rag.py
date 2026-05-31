# backend/app/rag.py
import os
import json
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from .config import Settings
from .llm import get_llm
from .vectorstore import get_vectorstore

_BASE_SYSTEM = """You are a creator analytics assistant comparing two short-form videos: Video A (YouTube) and Video B (Instagram Reel).

Use the provided transcript chunks AND the metadata stats below to answer. When citing transcript content, use [Video X, chunk N]. Always use the exact numbers from the metadata when answering engagement questions.

Important: Instagram's public API does not expose Reel view counts or follower counts without a verified login session. If Video B shows views=0 or followers=None, treat these as unavailable (not as actual zeros) and note this limitation in your answer. Use likes and comments as the available engagement signals for Video B.

Be concise, concrete, and reference specific lines from the transcripts when comparing hooks, pacing, or content."""

_memory = ConversationBufferWindowMemory(k=10, return_messages=True, memory_key="history")


def _load_metadata_block(data_dir: str) -> str:
    path = os.path.join(data_dir, "metadata.json")
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        meta = json.load(f)
    lines = ["\n## Video Metadata"]
    for vid_id, m in meta.items():
        lines.append(
            f"Video {vid_id} ({m.get('platform','')}) — "
            f"creator: {m.get('creator','?')}, "
            f"views: {m.get('views', 0):,}, "
            f"likes: {m.get('likes', 0):,}, "
            f"comments: {m.get('comments', 0):,}, "
            f"followers: {m.get('followers') or '?'}, "
            f"duration: {m.get('duration') or '?'}s, "
            f"engagement rate: {m.get('engagement_rate', 0)}%"
        )
    return "\n".join(lines)


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

    metadata_block = _load_metadata_block(settings.data_dir)
    system_prompt = _BASE_SYSTEM + metadata_block

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "Transcript chunks:\n{context}\n\nQuestion: {question}"),
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
