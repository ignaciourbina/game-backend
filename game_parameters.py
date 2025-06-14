# game_parameters.py
import os
from pathlib import Path

# Maximum number of players allowed in a session (defaults to 2)
MAX_PLAYERS = int(os.getenv("MAX_PLAYERS", "2"))

# Comma-separated list of valid moves for the game
CHOICES = os.getenv("CHOICES", "Cooperate,Defect").split(",")

# Location of the SQLite database file
DB_FILE = Path(os.getenv("GAME_DB_FILE", "/data/game.db"))

# Title shown in the FastAPI docs
APP_TITLE = os.getenv("APP_TITLE", "Two-Player Game API")
