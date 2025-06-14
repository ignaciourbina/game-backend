## Technical Report: Game Flow Design and Wait Handling

### 1. Overview

This report provides a deep dive into the multiplayer game backend we designed using FastAPI and SQLite. It focuses on the **game flow**, the **phase-based wait-handling mechanism**, and how the architecture guarantees synchronized progress across players.

---

### 2. Architecture Components

* **FastAPI**: Exposes RESTful endpoints for session management, state queries, move submissions, and result retrieval.
* **Uvicorn**: ASGI server that runs the FastAPI application.
* **SQLite**: File-based database storing session and move data.
* **Pydantic**: Schemas for request validation (e.g., `MoveIn`).
* **Database Helper (`game_db.py`)**: Context-managed connection, schema initialization, and core logic functions (`join_session`, `get_state`, `save_move`, `get_results`).

---

### 3. Database Schema

```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  player_count INTEGER NOT NULL CHECK(player_count BETWEEN 0 AND MAX_PLAYERS)
);

CREATE TABLE moves (
  session_id TEXT,
  player_id TEXT,
  choice TEXT,
  UNIQUE(session_id, player_id),
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
```

* `sessions`: tracks only the number of players joined.
* `moves`: records each unique player move per session.

---

### 4. API Endpoints

| Method | Path           | Description                                                    |
| ------ | -------------- | -------------------------------------------------------------- |
| POST   | `/api/join`    | Creates or joins a session; returns `session_id`, `player_id`. |
| GET    | `/api/state`   | Returns `{ players, moves, phase }`.                           |
| POST   | `/api/move`    | Accepts a player move (`MoveIn`); returns updated state.       |
| GET    | `/api/result`  | Retrieves ordered move history for a session.                  |
| GET    | `/api/dataset` | Streams raw SQLite file (`game.db`).                           |
| DELETE | `/api/dataset` | Clears and reinitializes the database.                         |

---

### 5. Phase Computation and Wait Gates

Synchronization hinges on deriving a **phase** from current counts:

```python
def get_state(session_id: str) -> StateOut:
    players = count_players(session_id)
    moves = count_moves(session_id)
    if players < MAX_PLAYERS:
        phase = "waiting_for_opponent"
    elif moves < players:
        phase = "waiting_for_moves"
    else:
        phase = "finished"
    return StateOut(players=players, moves=moves, phase=phase)
```

* **waiting\_for\_opponent**: gate until enough players join.
* **waiting\_for\_moves**: gate until every player has submitted.
* **finished**: no further moves allowed.

#### Enforcement in `save_move`

```python
def save_move(session_id, player_id, choice):
    state = get_state(session_id)
    if state.phase != "waiting_for_moves":
        raise ValueError("Not accepting moves in current phase")
    # UNIQUE constraint on (session_id, player_id) prevents duplicates
    cursor.execute(
      "INSERT INTO moves VALUES (?,?,?)", (session_id, player_id, choice)
    )
    conn.commit()
```

* Moves outside the `waiting_for_moves` phase are rejected.
* Duplicate submissions trigger a constraint error.

---

### 6. Client–Server Interaction Flow

1. **Join**: Client calls `POST /api/join`; server either creates a new session or increments `player_count`.
2. **Wait for Opponent**: Until `player_count == MAX_PLAYERS`, clients polling `GET /api/state` see `phase = "waiting_for_opponent"`.
3. **Submit Move**: Once enough players joined, each client calls `POST /api/move` with their choice.
4. **Wait for Moves**: After one player posts, the other sees `phase = "waiting_for_moves"` until their move arrives.
5. **Finish**: Once `moves == players`, `phase = "finished"`; clients retrieve results via `GET /api/result`.

---

### 7. Concurrency Considerations

* **SQLite PRAGMA**: Enabled `journal_mode=WAL` for improved concurrent reads.
* **Thread-Safety**: Used `check_same_thread=False` on connect; managed connections per request via context manager.
* **Barrier Behavior**: The phase check in `save_move` prevents race conditions where a late joiner or extra move slips through.

---

### 8. Extensibility and Enhancements

* **Per-Player Metadata**: Add a `players` table to track join timestamps, readiness flags, or profile data.
* **Explicit State Machine**: Implement a dedicated FSM library (e.g., `transitions`) for richer phase transitions.
* **Advanced Wait Handling**: Push WebSocket notifications when gates open, rather than relying on polling.
* **Scaling Out**: Swap SQLite for a managed database (Postgres) to handle higher concurrency and persistence.

---

### 9. Conclusion

By deriving phases from simple count-based logic and enforcing gates on every request, this design ensures that players progress in lockstep through the game. The lightweight FastAPI + SQLite combo keeps the code minimal and transparent, while the wait-handling mechanism guarantees synchronized gameplay without a complex state machine.
