# ---------------- app.py ----------------
"""FastAPI backend for a tiny two-player game (e.g. Prisoner's Dilemma).
Run locally with:  uvicorn app:app --host 0.0.0.0 --port 8000
When deployed as a **FastAPI Space** on Hugging Face, the hosting platform
will launch it for you (no explicit `uvicorn` call is required).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TypedDict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import game_db as db  # the helper module created earlier

# --------------------------------------------------------------------------- #
# Initialisation
# --------------------------------------------------------------------------- #
app = FastAPI(title="Two-Player Game API")
db.init_db()

# allow any origin so the built-in index.html can be opened from file:// too
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Pydantic models
# --------------------------------------------------------------------------- #

class JoinResponse(TypedDict):
    session_id: str
    player_id: str


class MoveIn(BaseModel):
    session_id: str
    player_id: str
    choice: str


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@app.post("/api/join", response_model=JoinResponse)
def join() -> JoinResponse:
    """Find a session (or create one) and return IDs for both session & player."""
    session_id, player_id = db.join_session()
    return {"session_id": session_id, "player_id": player_id}


@app.get("/api/state")
def state(session_id: str):
    try:
        return db.get_state(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/move")
def move(m: MoveIn):
    try:
        db.save_move(m.session_id, m.player_id, m.choice)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return db.get_state(m.session_id)


@app.get("/api/result")
def result(session_id: str):
    return {"results": db.get_results(session_id)}

