
"""
game_db.py

A minimal SQLite-backed helper for games with up to
``game_parameters.MAX_PLAYERS`` participants (e.g. Rock‍Paper‍Scissors).

Key improvements over the original sketch
-----------------------------------------
* Context‍manager (`get_conn`) guarantees connections are always closed
  even when an exception occurs.
* PRAGMA `foreign_keys = ON` so `moves.session_id` respects the parent `sessions` row.
* `moves` has a `(session_id, player_id)` UNIQUE constraint so the same
  player cannot submit two moves for one game.
* `join_session()` now also returns a unique `player_id`, so callers have
  an opaque token they can pass back to `save_move()`.
* Extra safety checks raise clear `ValueError`s for illegal states
  (unknown session, session full, duplicate moves, etc.).
* Typed function signatures for easier integration & autocomplete.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Tuple

import game_parameters

# --------------------------------------------------------------------------- #
# Paths & helpers
# --------------------------------------------------------------------------- #
DB_FILE: Path = game_parameters.DB_FILE


@contextmanager
def _get_conn() -> sqlite3.Connection:
    """Yield a SQLite connection with `foreign_keys` enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Schema initialisation
# --------------------------------------------------------------------------- #

def init_db() -> None:
    """Ensure the on‍disk database and tables exist."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _get_conn() as conn:
        cur = conn.cursor()
        # Sessions (a game waiting for MAX_PLAYERS players)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id           TEXT PRIMARY KEY,
                player_count INTEGER NOT NULL DEFAULT 0
                                 CHECK(player_count BETWEEN 0 AND {max_p})
            )
            """
            .format(max_p=game_parameters.MAX_PLAYERS)
        )

        # Individual moves made inside a session
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS moves (
                session_id TEXT NOT NULL,
                player_id  TEXT NOT NULL,
                choice     TEXT NOT NULL,
                UNIQUE (session_id, player_id),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
            """
        )

        # Helpful index for frequent look‍ups
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_moves_session ON moves(session_id)"
        )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def join_session() -> Tuple[str, str]:
    """
    Find (or create) a session that has fewer than ``MAX_PLAYERS`` players and
    join it.

    Returns
    -------
    (session_id, player_id)
        Both are opaque UUID4 strings generated server‍side.
    """
    with _get_conn() as conn:
        cur = conn.cursor()

        player_id: str = str(uuid.uuid4())

        while True:
            # Attempt to find a session waiting for more players.
            cur.execute(
                """
                SELECT id, player_count
                FROM   sessions
                WHERE  player_count < ?
                ORDER BY player_count DESC
                LIMIT 1
                """,
                (game_parameters.MAX_PLAYERS,),
            )
            row = cur.fetchone()

            if row:
                session_id, pcount = row
                try:
                    cur.execute(
                        "UPDATE sessions SET player_count = player_count + 1 "
                        "WHERE id = ? AND player_count = ?",
                        (session_id, pcount),
                    )
                except sqlite3.IntegrityError as exc:
                    raise ValueError("Failed to join existing session") from exc

                if cur.rowcount == 1:
                    # Successfully joined this session.
                    return session_id, player_id
                # Lost a race – another join updated first. Retry search.
                continue

            # No open sessions → create one.
            session_id = str(uuid.uuid4())
            try:
                cur.execute(
                    "INSERT INTO sessions (id, player_count) VALUES (?, 1)",
                    (session_id,),
                )
            except sqlite3.IntegrityError:
                # Extremely unlikely UUID collision or race; retry.
                continue

            return session_id, player_id


def get_state(session_id: str) -> Dict[str, int | str]:
    """
    Return a high‍level view of the session: number of players, number of moves, phase.
    """
    with _get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT player_count FROM sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Unknown session_id: {session_id}")

        players: int = row[0]

        cur.execute("SELECT COUNT(*) FROM moves WHERE session_id = ?", (session_id,))
        moves: int = cur.fetchone()[0]

    # Decide phase
    if players < game_parameters.MAX_PLAYERS:
        phase = "waiting_for_opponent"
    elif moves < players:
        phase = "waiting_for_moves"
    else:
        phase = "finished"

    return {"players": players, "moves": moves, "phase": phase}


def save_move(session_id: str, player_id: str, choice: str) -> None:
    """
    Persist a single move for a given player inside a session.

    Raises
    ------
    ValueError
        If the session does not exist, or the session is already finished,
        or the player already submitted a move.
    """
    with _get_conn() as conn:
        cur = conn.cursor()

        # Ensure session exists & not finished
        state = get_state(session_id)
        if state["phase"] == "waiting_for_opponent":
            raise ValueError(
                f"Cannot submit moves until {game_parameters.MAX_PLAYERS} players have joined."
            )
        if state["phase"] == "finished":
            raise ValueError("Session already finished; no further moves accepted.")

        # Attempt insert
        try:
            cur.execute(
                """
                INSERT INTO moves (session_id, player_id, choice)
                VALUES (?, ?, ?)
                """,
                (session_id, player_id, choice),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Duplicate move or invalid session.") from exc


def get_results(session_id: str) -> List[Dict[str, str]]:
    """
    Fetch the list of moves for a session (order is insertion order).

    Returns
    -------
    [{"player": ..., "choice": ...}, ...]
    """
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT player_id, choice
            FROM   moves
            WHERE  session_id = ?
            ORDER BY ROWID
            """,
            (session_id,),
        )
        return [{"player": p, "choice": c} for p, c in cur.fetchall()]
