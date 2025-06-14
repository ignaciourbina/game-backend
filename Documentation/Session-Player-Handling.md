When a visitor clicks Join, the front‑end makes a POST /api/join request and stores the returned IDs in localStorage. The code in the HTML explicitly sets two storage keys:
```
const store      = window.localStorage;
const sessionKey = "pd_session_id";  // maps to sessions.id (UUID)
const playerKey  = "pd_player_id";   // maps to moves.player_id (UUID)
```
The join controller then posts to the API and persists the IDs so that refreshing or opening the page in the same browser tab keeps the same session/player:
```
document.getElementById("join-btn").onclick = async () => {
  // POST /api/join → returns new session_id + player_id
  const { session_id, player_id } = await fetch(`${API}/api/join`,
    { method: "POST" }).then(r => r.json());

  // Persist IDs for future refreshes
  store.setItem(sessionKey, session_id);
  store.setItem(playerKey,  player_id);
  goto("waiting-opponent");
};
```
On the server side, the /api/join endpoint simply calls db.join_session() and returns the IDs:
```
@app.post("/api/join", response_model=JoinResponse, status_code=200)
def join() -> JoinResponse:
    """`POST /api/join` – allocate a **session/player tuple**."""
    sid, pid = db.join_session()
    return {"session_id": sid, "player_id": pid}
```
join_session() in game_db.py looks for an open session (fewer than MAX_PLAYERS participants) and either joins it or creates a new one. A new player_id is generated for every call:
```
def join_session() -> Tuple[str, str]:
    ...
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
        ...
        return session_id, player_id
```
Thus, when you open index.html in two different browsers:

First browser: POSTs /api/join. Since no session exists yet, join_session() creates one with player_count = 1 and returns the new session ID and a new player ID.

Second browser: Its join call finds that session waiting for a second player (player count < MAX_PLAYERS, typically 2). It atomically increments player_count to 2 and returns the same session ID but a different player ID.

Those IDs are stored in each browser’s localStorage, so the page can keep polling /api/state or send a move via /api/move without rejoining. The README explicitly notes that “Each visitor auto‑pairs with the next visitor; phase logic lives in the DB.”

In short, the persistence comes from storing the IDs client‑side, and session assignment comes from the join_session() logic that matches players until a session is full before creating a new one.
