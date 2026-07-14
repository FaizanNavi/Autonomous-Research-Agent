import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .agents.orchestrator import ResearchOrchestrator
from .utils.config import HOST, PORT
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
app = FastAPI(
    title="Autonomous Research Agent",
    description="5-agent research system with reflection loops",
    version="1.0.0"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
orchestrator = ResearchOrchestrator()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

class ResearchRequest(BaseModel):
    topic: str = Field(..., description="Research topic or question")
    class Config:
        json_schema_extra = {"example": {"topic": "Impact of AI on job markets in 2025"}}
@app.get("/health")
async def health():
    return {"status": "ok", "service": "autonomous-research-agent"}
@app.post("/research")
async def research(request: ResearchRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    result = orchestrator.run(request.topic)
    return {
        "topic": request.topic,
        "report": result.get("final_report", ""),
        "iterations": result.get("iterations", 0),
        "critic_score": result.get("critic_report", {}).get("quality_score"),
        "status": result.get("status", "complete")
    }

# Serve frontend at root
@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Serve any other static assets from frontend/
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)

