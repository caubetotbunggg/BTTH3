#!/usr/bin/env bash
# smoke_test.sh: Kiểm thử nhanh sau khi deploy trên Render

set -euo pipefail

APP_URL="https://btth3.onrender.com"

echo "🔎 Running smoke tests on $APP_URL ..."

# Test endpoint /retrieve
echo "Testing /retrieve..."
curl -s -X POST "$APP_URL/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "test", "k": 1}' \
  | grep -q "chunks" || { echo "❌ /retrieve failed"; exit 1; }

# Test endpoint /agent
echo "Testing /agent..."
curl -s -X POST "$APP_URL/agent" \
  -H "Content-Type: application/json" \
  -d '{"query": "ping"}' \
  | grep -q "answer" || { echo "❌ /agent failed"; exit 1; }

echo "✅ Smoke tests passed!"
