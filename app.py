# ---------------- app.py ----------------
"""FastAPI backend (API *only*) for the two‑player game.

The frontend lives elsewhere, so we **do not** serve static files.
Deploy this file in a Hugging Face *FastAPI Space* or *Docker Space* –
the platform will detect the `app` object automatically.
"""

from __future__ import annotations

import uuid
from typing import TypedDict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import game_db as db  # database helper module

# --------------------------------------------------------------------------- #
# Initialisation
# --------------------------------------------------------------------------- #
app = FastAPI(title="Two‑Player Game API")
db.init_db()

# Allow any origin so an external HTML page can call our API via fetch()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your domain if desired
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
    """Create or join a session and return IDs for session & player."""
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