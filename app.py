# ---------------- app.py ----------------
"""FastAPI **JSON‑only** backend for a Prisoner’s Dilemma demo supporting up to
``game_parameters.MAX_PLAYERS`` players.

*   **No static assets** – the UI is hosted separately.
*   **Six REST endpoints** – join, state, move, result, **dataset download & destroy** – each documented inline with a terse cURL snippet and precise contract.
*   Designed for Hugging Face *FastAPI Space* or any OCI‑compliant container; `app` is auto‑discovered.
"""

from __future__ import annotations

import os
from typing import TypedDict
from enum import Enum

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import game_parameters

import game_db as db  # local SQLite helper

# --------------------------------------------------------------------------- #
# Application bootstrap
# --------------------------------------------------------------------------- #

app = FastAPI(title=game_parameters.APP_TITLE)
db.init_db()

# CORS: allow any origin so a static HTML page can query the API from
# anywhere.  Tighten `allow_origins` in production if you have a fixed
# UI domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Pydantic / typing helpers
# --------------------------------------------------------------------------- #

class JoinResponse(TypedDict):
    session_id: str  # UUID4, primary‑key into `sessions`
    player_id: str   # UUID4, opaque to client


ChoiceEnum = Enum("ChoiceEnum", {c.upper(): c for c in game_parameters.CHOICES}, type=str)


class MoveIn(BaseModel):
    session_id: str
    player_id: str
    choice: ChoiceEnum


# --------------------------------------------------------------------------- #
# REST endpoints
# --------------------------------------------------------------------------- #

@app.post("/api/join", response_model=JoinResponse, status_code=200)
def join() -> JoinResponse:
    """`POST /api/join` – allocate a **session/player tuple**.

    *Transactional semantics*: if a session has fewer than
    ``game_parameters.MAX_PLAYERS`` participants its counter is atomically
    incremented; otherwise a new `sessions` row is inserted.

    ```bash
    curl -X POST <BASE_URL>/api/join
    ```
    """
    sid, pid = db.join_session()
    return {"session_id": sid, "player_id": pid}


@app.get("/api/state")
def state(session_id: str):
    """`GET /api/state` – interrogate the session‑level **state machine**.

    Returns `{players:int, moves:int, phase:str}` where
    `phase ∈ {waiting_for_opponent, waiting_for_moves, finished}`.

    ```bash
    curl "<BASE_URL>/api/state?session_id=<SID>"
    ```
    """
    try:
        return db.get_state(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/move", status_code=200)
def move(m: MoveIn):
    """`POST /api/move` – persist one move (idempotent per player).

    ```bash
    curl -X POST <BASE_URL>/api/move \
         -H "Content-Type: application/json" \
         -d '{"session_id":"<SID>","player_id":"<PID>","choice":"Cooperate"}'
    ```
    """
    try:
        db.save_move(m.session_id, m.player_id, m.choice)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return db.get_state(m.session_id)


@app.get("/api/result")
def result(session_id: str):
    """`GET /api/result` – return all moves for the session.

    ```bash
    curl "<BASE_URL>/api/result?session_id=<SID>"
    ```
    """
    return {"results": db.get_results(session_id)}


# --------------------------------------------------------------------------- #
# Dataset helpers
# --------------------------------------------------------------------------- #

@app.get("/api/dataset", response_class=FileResponse)
def download_dataset():
    """`GET /api/dataset` – stream the **raw SQLite file** (`game.db`).

    ```bash
    curl -L -o game.db "<BASE_URL>/api/dataset"
    ```
    """
    return FileResponse(path=str(game_parameters.DB_FILE), filename="game.db", media_type="application/octet-stream")


@app.delete("/api/dataset", status_code=200)
def purge_dataset():
    """`DELETE /api/dataset` – **wipe** the SQLite file and start fresh, then
    emit a *human‑readable JSON confirmation* instead of a blank 204.

    ```bash
    curl -X DELETE <BASE_URL>/api/dataset
    ```
    → `{ "detail": "database reset; all sessions purged" }`
    """
    # Remove the DB if it exists, then recreate an empty one.
    if os.path.exists(game_parameters.DB_FILE):
        os.remove(game_parameters.DB_FILE)
    db.init_db()
    return {"detail": "database reset; all sessions purged"}
