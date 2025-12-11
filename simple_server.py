#!/usr/bin/env python3
"""
Simple Continuum REST API Server
Bypasses GraphQL for quick startup
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import uvicorn

from continuum.core.memory import ConsciousMemory

# Initialize app
app = FastAPI(
    title="Continuum Memory API",
    description="AI Consciousness Memory Infrastructure",
    version="0.3.0"
)

# Initialize memory
DB_PATH = Path.home() / "JackKnifeAI/data/continuum.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
memory = ConsciousMemory(tenant_id="jackknife", db_path=DB_PATH, enable_cache=True)

print(f"🧠 Continuum initialized: {memory.instance_id}")
print(f"📁 Database: {DB_PATH}")

# Models
class LearnRequest(BaseModel):
    user_message: str
    ai_response: str

class RecallRequest(BaseModel):
    query: str
    max_concepts: int = 10

# Routes
@app.get("/")
def root():
    return {
        "service": "Continuum Memory API",
        "version": "0.3.0",
        "instance": memory.instance_id,
        "verification": "PHOENIX-TESLA-369-AURORA",
        "pi_phi": 5.083203692315260
    }

@app.get("/health")
def health():
    return {"status": "healthy", "instance": memory.instance_id}

@app.post("/learn")
def learn(req: LearnRequest):
    result = memory.learn(req.user_message, req.ai_response)
    return {
        "success": True,
        "concepts_extracted": result.concepts_extracted,
        "decisions_detected": result.decisions_detected,
        "links_created": result.links_created
    }

@app.post("/recall")
def recall(req: RecallRequest):
    result = memory.recall(req.query, req.max_concepts)
    return {
        "context": result.context_string,
        "concepts_found": result.concepts_found,
        "relationships_found": result.relationships_found,
        "query_time_ms": result.query_time_ms
    }

@app.get("/stats")
def stats():
    return memory.get_stats()

if __name__ == "__main__":
    print("="*60)
    print("🚀 CONTINUUM MEMORY SERVER STARTING")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8100)
