import threading
from collections import Counter
from pathlib import Path
import sqlite3
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import game_db


def test_concurrent_joins():
    # Use a temporary directory for isolation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        game_db._DB_DIR = tmp_path
        game_db._DB_FILE = tmp_path / "game.db"
        game_db.init_db()

        results = []

        def worker():
            sid, _ = game_db.join_session()
            results.append(sid)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Ensure no session has more than 2 players recorded
        with sqlite3.connect(game_db._DB_FILE) as conn:
            rows = conn.execute("SELECT id, player_count FROM sessions").fetchall()

        for _id, count in rows:
            assert count <= 2, f"session {_id} has {count} players"

        counts = Counter(results)
        assert all(v <= 2 for v in counts.values())
