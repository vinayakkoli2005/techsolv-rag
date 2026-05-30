# backend/app/routes.py
import os
import json
import asyncio
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from .config import settings
from .schemas import IngestRequest, IngestResponse, ChatRequest
from .ingest import ingest_pair
from .rag import build_rag_chain

router = APIRouter(prefix="/api")

_rag_state = {"chain": None, "memory": None}

@router.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    try:
        result = ingest_pair(str(req.youtube_url), str(req.instagram_url))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    chain, _retriever, memory = build_rag_chain(settings)
    _rag_state["chain"] = chain
    _rag_state["memory"] = memory
    return result

@router.get("/metadata")
def metadata():
    path = os.path.join(settings.data_dir, "metadata.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No ingested videos yet")
    with open(path) as f:
        return json.load(f)

@router.post("/chat")
async def chat(req: ChatRequest):
    if _rag_state["chain"] is None:
        chain, _r, memory = build_rag_chain(settings)
        _rag_state["chain"] = chain
        _rag_state["memory"] = memory

    chain = _rag_state["chain"]
    memory = _rag_state["memory"]
    question = req.question

    async def event_stream():
        full = []
        try:
            async for token in chain.astream({"question": question}):
                full.append(token)
                yield {"event": "token", "data": json.dumps({"text": token})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            return
        answer = "".join(full)
        memory.save_context({"input": question}, {"output": answer})

        from .vectorstore import get_vectorstore
        vs = get_vectorstore(settings, collection_name="videos")
        docs = vs.similarity_search(question, k=6)
        citations = [
            {"video_id": d.metadata.get("video_id"), "chunk_index": d.metadata.get("chunk_index")}
            for d in docs
        ]
        yield {"event": "citations", "data": json.dumps({"citations": citations})}
        yield {"event": "done", "data": json.dumps({})}

    return EventSourceResponse(event_stream())
