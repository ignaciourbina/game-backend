
# 1) open the DB file directly
sqlite3 game.db

-- now you're at the sqlite> prompt and the file is already attached --

# 2) optional: make results readable
.headers on      -- show column names
.mode column     -- nice aligned columns   (or .mode box on modern SQLite)

# 3) dump the table
SELECT * FROM moves;

# 4) leave the shell
.quit


---


You’re already inside the SQLite interactive shell, so the extra `sqlite3 game.db ".tables"` just tried to **launch a second shell inside the first one**—that’s why nothing happened.
Here are two clean ways to inspect the file:

---

### Option 1 – Open the DB at launch

```cmd
sqlite3.exe game.db
```

Inside the prompt:

```sqlite
.tables         -- lists tables
SELECT * FROM sessions;
SELECT * FROM moves;
.quit
```

---

### Option 2 – Open from an existing prompt

If you’ve already started `sqlite3` and see `sqlite>`, simply do:

```sqlite
.open game.db    -- attaches the file
.tables
```

(You can verify with `.database`.)

---

### Common quick commands

| Command                        | Purpose                   |
| ------------------------------ | ------------------------- |
| `.tables`                      | list table names          |
| `.schema moves`                | show DDL for a table      |
| `.headers on` + `.mode column` | pretty-print query output |
| `.exit` or `.quit`             | leave the shell           |

With that you’ll see the same four-row `moves` table you saw in the web viewer.


SQLite CLI – Quick‑Reference Snippet

1  Launch & basic navigation

sqlite3 game.db         # open DB file
.open game.db           # (inside shell) attach file if you started without one
.tables                 # list tables
.schema          # show CREATE TABLE DDL
.headers on             # show column names in results
.mode column            # nice aligned output

2  Common queries for the PD game
```sqlite
SELECT * FROM sessions;
SELECT * FROM moves;

-- Count moves & cooperation rate
SELECT COUNT() AS total_moves,
SUM(choice = 'Cooperate') AS cooperates,
ROUND(100.0 * SUM(choice = 'Cooperate') / COUNT(), 1) || '%' AS coop_rate
FROM moves;

-- Per‑session summary
SELECT s.id,
s.player_count,
COUNT(m.choice) AS moves_made,
SUM(m.choice = 'Cooperate') AS coop,
SUM(m.choice = 'Defect')    AS defect
FROM sessions s
LEFT JOIN moves m ON m.session_id = s.id
GROUP BY s.id;
```
3  Export to CSV / JSON
```sqlite
.mode csv
.headers on
.output moves.csv
SELECT * FROM moves;
.output stdout          # reset output target

-- One‑liner CSV export (outside shell)
sqlite3 -header -csv game.db "SELECT * FROM moves;" > moves.csv

-- JSON export (SQLite ≥3.38)
sqlite3 -json game.db "SELECT json_group_array(json_object('session',session_id,'player',player_id,'choice',choice)) FROM moves;" > moves.json
```
4  Exit shell
```sqlite
.quit                    # or .exit

```
