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

---

When a round finishes, the Results page activates the Play again button.
The handler for that button is defined in the client:
```
248          // Restart wipes IDs and returns to Join page
249          document.getElementById("restart-btn").onclick = () => {
250            resetLocal();
251            goto("join");
252          };
```
resetLocal() simply clears the stored identifiers:
```
139      /** Clear localStorage copy of session & player IDs. */
140      function resetLocal() {
141        store.removeItem(sessionKey);
142        store.removeItem(playerKey);
143      }
```
After the IDs are wiped, the user is sent back to the Join page.
There, clicking Join triggers a new request to /api/join:
```
150        /* -------------------------------------------------- JOIN PAGE ----- */
151        "join": () => {
...
159          document.getElementById("join-btn").onclick = async () => {
160            // POST /api/join → returns new session_id + player_id
161            const { session_id, player_id } = await fetch(`${API}/api/join`,
162              { method: "POST" }).then(r => r.json());
163
164            // Persist IDs for future refreshes
165            store.setItem(sessionKey, session_id);
166            store.setItem(playerKey,  player_id);
167            goto("waiting-opponent");
168          };
```
On the server, join_session() either places the player in a waiting session or starts a new one:
```
94  def join_session() -> Tuple[str, str]:
...
107      player_id: str = str(uuid.uuid4())
...
110              # Attempt to find a session waiting for more players.
...
134                  if cur.rowcount == 1:
135                      # Successfully joined this session.
136                      return session_id, player_id
...
140              # No open sessions → create one.
141              session_id = str(uuid.uuid4())
...
151              return session_id, player_id
```

Therefore, clicking Play again just clears the current session/player IDs and routes the browser back to the Join page. The next click on Join causes a new /api/join request, which allocates a fresh player ID and either reuses an open session or creates a new one. The previous (finished) session remains in the database, while the player enters a new session as if starting from scratch.


