set -euo pipefail

APP_URL="${APP_URL:-https://btth3.onrender.com}"

echo "🔎 Running smoke tests on $APP_URL ..."

fail() {
  echo "❌ $1"
  exit 1
}

# ---------- 1. /health ----------
echo "➡ Testing /health..."
health=$(curl -s -f "$APP_URL/health") || fail "/health unreachable"
echo "$health" | grep -q '"status":' || fail "/health missing 'status' field"

# ---------- 2. /retrieve ----------
echo "➡ Testing /retrieve..."
retrieve=$(curl -s -f -X POST \
  "$APP_URL/retrieve?user_input=Hi&k=1") || fail "/retrieve request failed"
echo "$retrieve" | grep -q "chunks" || fail "/retrieve response missing 'chunks'"

# ---------- 3. /rag ----------
echo "➡ Testing /rag..."
rag=$(curl -s -f -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_input":"hello","k":1}' \
  "$APP_URL/rag") || fail "/rag request failed"
echo "$rag" | grep -q "answer" || fail "/rag response missing 'answer'"

# ---------- 4. /agent ----------
echo "➡ Testing /agent..."
agent=$(curl -s -f -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_input":"law test","k":1,"max_steps":2}' \
  "$APP_URL/agent") || fail "/agent request failed"
echo "$agent" | grep -q "status" || fail "/agent response missing 'status'"

echo "✅ All smoke tests passed successfully!"
