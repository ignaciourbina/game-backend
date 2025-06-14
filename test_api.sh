#!/usr/bin/env bash
# --------------------------------------------------------------------------- #
# test_api.sh – quick‑and‑dirty harness that exercises the Five‑Endpoint
#               Prisoner’s Dilemma API with **four players** (two sessions)
#               and finally dumps the raw SQLite database.
#
#   • Requires: curl, jq  (brew install jq | apt‑get install jq)
#   • Usage   : ./test_api.sh [BASE_URL]
#               BASE_URL defaults to the HF Space demo URL.
# --------------------------------------------------------------------------- #
set -euo pipefail

BASE_URL=${1:-"https://iurbinah-pd-backend-api.hf.space"}

echo "=== 1. Spawning Session #1 ==="
resp=$(curl -s -X POST "$BASE_URL/api/join")
SID1=$(echo "$resp" | jq -r .session_id)
PID1=$(echo "$resp" | jq -r .player_id)

echo "Session 1: Player A ($PID1) joined (session $SID1)"

resp=$(curl -s -X POST "$BASE_URL/api/join")
SID1b=$(echo "$resp" | jq -r .session_id)
PID2=$(echo "$resp" | jq -r .player_id)

echo "Session 1: Player B ($PID2) joined (session $SID1b)"

if [[ "$SID1b" != "$SID1" ]]; then
  echo "❌ Unexpected: second join did not land in same session" >&2
  exit 1
fi

echo "Submitting moves for Session 1…"
curl -s -X POST "$BASE_URL/api/move" \
     -H 'Content-Type: application/json' \
     -d '{"session_id":"'$SID1'","player_id":"'$PID1'","choice":"Cooperate"}' > /dev/null
curl -s -X POST "$BASE_URL/api/move" \
     -H 'Content-Type: application/json' \
     -d '{"session_id":"'$SID1'","player_id":"'$PID2'","choice":"Defect"}' > /dev/null

echo "=== 2. Spawning Session #2 ==="
resp=$(curl -s -X POST "$BASE_URL/api/join")
SID2=$(echo "$resp" | jq -r .session_id)
PID3=$(echo "$resp" | jq -r .player_id)

echo "Session 2: Player C ($PID3) joined (session $SID2)"

resp=$(curl -s -X POST "$BASE_URL/api/join")
SID2b=$(echo "$resp" | jq -r .session_id)
PID4=$(echo "$resp" | jq -r .player_id)

echo "Session 2: Player D ($PID4) joined (session $SID2b)"

if [[ "$SID2b" != "$SID2" ]]; then
  echo "❌ Unexpected: second join did not land in same session" >&2
  exit 1
fi

echo "Submitting moves for Session 2…"
curl -s -X POST "$BASE_URL/api/move" \
     -H 'Content-Type: application/json' \
     -d '{"session_id":"'$SID2'","player_id":"'$PID3'","choice":"Defect"}' > /dev/null
curl -s -X POST "$BASE_URL/api/move" \
     -H 'Content-Type: application/json' \
     -d '{"session_id":"'$SID2'","player_id":"'$PID4'","choice":"Cooperate"}' > /dev/null

echo "=== 3. Downloading raw SQLite payload ==="
curl -L -o game.db "$BASE_URL/api/dataset"

echo "✅  All done – game.db contains both sessions & their moves."
