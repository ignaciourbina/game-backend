# 🕊️ Prisoner’s‑Dilemma Mini‑Stack

A **zero‑dependency front‑end** + **FastAPI/SQLite back‑end** that lets visitors play a one‑shot Prisoner’s Dilemma in real time. The number of players defaults to two and can be changed via the `MAX_PLAYERS` environment variable — perfect for demos, behavioural‑econ labs, or multiplayer tutorials.

---

## ✨ What’s inside?

| Layer          | Tech & File(s)                                     | Purpose                                                                                                                                                                  |
| -------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **UI**         | [`index.html`](./index.html)                       | Single‑page hash‑router (vanilla JS) that calls the API and renders five pseudo‑pages: *Join → Wait → Play → Wait → Results*. No build step needed.                      |
| **API**        | [`app.py`](./app.py)                               | FastAPI with six REST endpoints – `/join`, `/state`, `/move`, `/result`, `/dataset` (**GET** download, **DELETE** purge). Runs in a HF *FastAPI* Space or any container. Title configurable via `APP_TITLE`. |
| **Data**       | [`game_db.py`](./game_db.py)                       | Thin SQLite helper (path via `GAME_DB_FILE`, default /data/game.db) with safety rails: context‑managed connections, foreign keys, unique constraints. Valid moves are read from `CHOICES`.                                                   |
| **Tests**      | [`test_api.sh`](./test_api.sh)                     | Bash harness that spawns two sessions (`MAX_PLAYERS` players each by default), submits moves, and downloads the DB.                                                                               |
| **SQL cheats** | [`sqlite_cheatsheet.md`](./sqlite_cheatsheet.md) | Copy‑paste SQLite commands for inspection & export.                                                                                                                      |

---

## 🏗 Architecture

```
┌───────── static host ─────────┐      ┌──────── Hugging Face Space ───────┐
│  index.html  (UI)             │ ───▶ │  FastAPI  (app.py)               │
│  JS  fetch('/api/*')          │ ◀─── │  SQLite   (game_db.py)           │
└───────────────────────────────┘      └───────────────────────────────────┘
```

*Front‑end can live anywhere (GitHub Pages, Netlify, HF Static). Back‑end exposes JSON only; no static assets served.*

---

## 🚀 Quick start (local)

```bash
# clone + install deps
python -m venv venv && source venv/bin/activate
pip install fastapi[all] uvicorn

# optional customisation
export MAX_PLAYERS=2                   # players per session
export CHOICES="Cooperate,Defect"      # valid moves
export GAME_DB_FILE=/data/game.db      # SQLite path
export APP_TITLE="Two-Player Game API" # docs label

# launch API (creates DB if needed)
uvicorn app:app --reload --port 8000
#                ↑ 0.0.0.0 for Docker

# serve the UI from any static server
python -m http.server 5500  # then open http://localhost:5500/index.html
```

---

### Deploy to Hugging Face

1. **Back‑end** – create a *FastAPI Space*; drop `app.py` & `game_db.py` in repo root.
2. **Front‑end** – create a *Static Space* (or GitHub Pages) with `index.html`.
3. Edit the `API` constant inside `index.html` to the back‑end Space URL.

Each visitor auto‑pairs with the next visitor; phase logic lives in the DB.

---

## 📬 API Reference

| Verb & Route              | Purpose                             | Body / Query                        | Success (200)                                       |
| ------------------------- | ----------------------------------- | ----------------------------------- | --------------------------------------------------- |
| **POST** `/api/join`      | Open or join a session; returns IDs | –                                   | `{ session_id, player_id }`                         |
| **GET** `/api/state`      | Poll phase                          | `session_id`                        | `{ players, moves, phase }`                         |
| **POST** `/api/move`      | Submit choice                       | `{ session_id, player_id, choice }` | same as `/state`                                    |
| **GET** `/api/result`     | Fetch both moves                    | `session_id`                        | `{ results:[{player,choice},…] }`                   |
| **GET** `/api/dataset`    | Download raw DB                     | –                                   | file from `GAME_DB_FILE`                                  |
| **DELETE** `/api/dataset` | Reset DB (testing)                  | –                                   | `{ detail: "database reset; all sessions purged" }` |

**Cheat‑curl**

```bash
curl -X POST <API>/api/join
curl "<API>/api/state?session_id=<SID>"
curl -X POST <API>/api/move -H "Content-Type: application/json" \
     -d '{"session_id":"<SID>","player_id":"<PID>","choice":"Cooperate"}'
curl "<API>/api/result?session_id=<SID>"
curl -o my.db <API>/api/dataset        # file from `GAME_DB_FILE`
curl -X DELETE <API>/api/dataset   # wipe
```

---

## 🔬 Data inspection

```bash
sqlite3 $GAME_DB_FILE ".tables"                     # sessions moves
sqlite3 $GAME_DB_FILE "SELECT choice,COUNT(*) FROM moves GROUP BY choice;"
```

See [`sqlite_cheatsheet.txt`](./sqlite_cheatsheet.txt) or the *SQLite Starter Pack* canvas for more.

---

## 🧪 End‑to‑end smoke test

```bash
# spins up two sessions with demo moves, then downloads the DB
bash test_api.sh https://<backend-space>.hf.space
```

Should end with ✅ and a SQLite file (from `GAME_DB_FILE`) of \~20–30 KB.

---

## 🤝 Extending

* Add payoff matrix & score endpoint
* WebSocket push instead of polling
* Auth layer to track real users
* Front‑end polish (React/Svelte, charts, etc.)
* Analytics snapshots via cron + SQL

PRs welcome!

---

## 🌱 Roadmap

For the longer-term vision of turning this demo into a reusable module and zero-code builder, see [ROADMAP.md](./ROADMAP.md).

---

## 📄 License

MIT – do whatever you like, attribution appreciated.
