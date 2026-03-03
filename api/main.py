"""
api/main.py — AskOps by RaveMinds
Returns all 4 views. Supports /ask/stream for incremental progress.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog

from agent.graph import ask, build_graph

log = structlog.get_logger()

app = FastAPI(
    title="AskOps by RaveMinds",
    description="Ask your infrastructure anything.",
    version="2.0.0",
)

class AskRequest(BaseModel):
    user_id:  str
    question: str

class AskResponse(BaseModel):
    business:   str
    manager:    str
    technical:  str
    full:       str
    trade_id:   str
    user_id:    str
    question:   str
    latency_ms: int

@app.get("/health")
async def health():
    return {"status": "ok", "service": "askops-api", "version": "2.0.0"}

def _strip_slack_mentions(text: str) -> str:
    return re.sub(r"<@[A-Z0-9]+>", "", text).strip()


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest):
    question = _strip_slack_mentions(req.question)
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    log.info("question_received", user_id=req.user_id, question=question)
    start  = time.time()
    result = ask(question)
    latency_ms = int((time.time() - start) * 1000)

    log.info("answer_generated", user_id=req.user_id, latency_ms=latency_ms)

    return AskResponse(
        business=result["business"], manager=result["manager"],
        technical=result["technical"], full=result["full"],
        trade_id=result["trade_id"], user_id=req.user_id,
        question=question, latency_ms=latency_ms,
    )


@app.post("/ask/stream")
async def ask_stream_endpoint(req: AskRequest):
    """SSE stream: progress events then final result."""
    question = _strip_slack_mentions(req.question)
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    def generate():
        from agent.graph import _extract_trade_id
        trade_id = _extract_trade_id(question)
        graph = build_graph()
        start = time.time()
        init = {"question": question, "trade_id": trade_id, "raw_data": {}, "historical": "",
                "view_business": "", "view_manager": "", "view_technical": "", "view_full": ""}

        yield f"data: {json.dumps({'event': 'progress', 'stage': 'started'})}\n\n"
        for chunk in graph.stream(init, stream_mode="updates"):
            for node, data in chunk.items():
                if node == "data_collector":
                    yield f"data: {json.dumps({'event': 'progress', 'stage': 'data_ready', 'trade_id': trade_id})}\n\n"
                elif node == "combined_views" and data.get("view_business"):
                    result = {
                        "event": "result",
                        "business": data["view_business"],
                        "manager": data["view_manager"],
                        "technical": data["view_technical"],
                        "full": data["view_full"],
                        "trade_id": trade_id,
                        "latency_ms": int((time.time() - start) * 1000),
                    }
                    yield f"data: {json.dumps(result)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8001, reload=True)
