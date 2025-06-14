# ---------------- app.py ----------------
"""FastAPI **JSON‑only** backend for the two‑player Prisoner’s Dilemma demo.

*   **No static assets** – the UI is hosted separately.
*   **Five REST endpoints** – each documented inline with a terse cURL
    ready to paste and a *technical* contract (method, status codes,
    request/response schema).
*   Designed for Hugging Face *FastAPI Space* or any OCI‑compliant
    container; `app` is auto‑discovered.
"""

from __future__ import annotations

from typing import TypedDict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import game_db as db  # local SQLite helper

# --------------------------------------------------------------------------- #
# Application bootstrap
# --------------------------------------------------------------------------- #

app = FastAPI(title="Two‑Player Game API")
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


class MoveIn(BaseModel):
    session_id: str
    player_id: str
    choice: str  # "Cooperate" | "Defect"  (no enum for brevity)


# --------------------------------------------------------------------------- #
# REST endpoints
# --------------------------------------------------------------------------- #

@app.post("/api/join", response_model=JoinResponse, status_code=200)
def join() -> JoinResponse:
    """`POST /api/join` – allocate a **session/player tuple**.

    *   **Transactional semantics:**
        *If* a session exists with `player_count = 1` it is atomically
        updated to 2; otherwise a new `sessions` row is inserted with
        `player_count = 1`.
    *   **Returns:** `200 OK` + JSON body `{"session_id", "player_id"}`.
      Both are UUID4 strings generated server‑side.
    *   **Failure modes:** none (always succeeds).

    ```bash
    curl -X POST <BASE_URL>/api/join
    ```
    """
    sid, pid = db.join_session()
    return {"session_id": sid, "player_id": pid}


@app.get("/api/state")
def state(session_id: str):
    """`GET /api/state` – interrogate a session‑level **state machine**.

    *   **Query params:** `session_id=<uuid4>`.
    *   **Response (200):** JSON with keys
        `{players:int, moves:int, phase:str}` where `phase ∈ {waiting_for_opponent, waiting_for_moves, finished}`.
    *   **404** if `session_id` is unknown / expired.

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
    """`POST /api/move` – persist a **single move** (idempotent per player).

    *   **Body:** JSON matching `MoveIn` (see above).
    *   **Transactional guards:**
        * duplicate move ➜ `400 Bad Request`
        * session not at 2 players ➜ `400`
        * session already finished ➜ `400`
    *   **Success payload (200):** same shape as `/api/state` so the UI
        can refresh phase without an extra request.

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
    """`GET /api/result` – list **all moves** in insertion order.

    *   **200 OK:** `{ "results": [ {"player", "choice"}, … ] }`.
        Only available once `phase == finished`; caller must poll `/api/state`.
    *   **No error branch:** if game isn’t finished you still get the
        partial array – the front‑end treats phase as the gatekeeper.

    ```bash
    curl "<BASE_URL>/api/result?session_id=<SID>"
    ```
    """
    return {"results": db.get_results(session_id)}


# --------------------------------------------------------------------------- #
# Data‑export helper
# --------------------------------------------------------------------------- #

@app.get("/api/dataset", response_class=FileResponse)
def download_dataset():
    """`GET /api/dataset` – stream the **raw SQLite file** (`game.db`).

    Useful for offline analytics or debugging.  The route sets
    `Content‑Disposition: attachment; filename=game.db` so browsers
    download instead of preview.

    ```bash
    curl -L -o game.db "<BASE_URL>/api/dataset"
    ```
    """
    return FileResponse(path=str(db._DB_FILE), filename="game.db", media_type="application/octet-stream")
