from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .adk_runtime import run_agent_task
from .persistence import load_workflow, persist_workflow
from .workflow import PolicyViolation, workflow_store

app = FastAPI(title="Driftline API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ApprovalRequest(BaseModel):
    approver: str
    decision: str = "grandfather_existing_customers"


class UndoRequest(BaseModel):
    actor: str


class AgentRunRequest(BaseModel):
    query: str
    user_id: str = "demo-operator"


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "driftline-agent",
        "persistence": os.getenv("DRIFTLINE_PERSISTENCE", "memory"),
    }


def _resolve_workflow(workflow_id: str):
    try:
        return workflow_store.get(workflow_id)
    except KeyError:
        state = load_workflow(workflow_id)
        if state is not None:
            return workflow_store.restore(state)
        raise


@app.post("/api/workflows/demo")
def start_demo() -> dict:
    state = workflow_store.start_demo()
    persist_workflow(state)
    return state.to_dict()


@app.post("/api/agent/run")
async def run_agent(request: AgentRunRequest) -> dict:
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")
    try:
        return await run_agent_task(request.query, request.user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Live ADK execution is unavailable; check Google Cloud credentials.",
        ) from exc


@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: str) -> dict:
    try:
        return _resolve_workflow(workflow_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/approve")
def approve(workflow_id: str, request: ApprovalRequest) -> dict:
    try:
        _resolve_workflow(workflow_id)
        state = workflow_store.approve(
            workflow_id,
            request.approver,
            request.decision,
        )
        persist_workflow(state)
        return state.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/undo")
def undo(workflow_id: str, request: UndoRequest) -> dict:
    try:
        _resolve_workflow(workflow_id)
        state = workflow_store.undo(workflow_id, request.actor)
        persist_workflow(state)
        return state.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


static_dir = Path(os.getenv("DRIFTLINE_STATIC_DIR", "/app/static"))
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="console")
