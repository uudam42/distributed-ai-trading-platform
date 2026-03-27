#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8090}"
ALICE_EMAIL="alice@example.com"
BOB_EMAIL="bob@example.com"
PASSWORD="password123"
ALICE_ACCOUNT_ID="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
BOB_ACCOUNT_ID="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
INSTRUMENT="BTC-USD"
PRICE="100.0"
QTY="1.0"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Error: missing dependency '$1'"; exit 1; }
}
need curl
need jq

call_json() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  local auth="${4:-}"
  local tmp_body tmp_code
  tmp_body=$(mktemp)
  tmp_code=$(mktemp)
  trap 'rm -f "$tmp_body" "$tmp_code"' RETURN

  if [[ -n "$body" && -n "$auth" ]]; then
    curl -sS -X "$method" "$url" -H 'content-type: application/json' -H "authorization: Bearer $auth" -d "$body" -o "$tmp_body" -w '%{http_code}' > "$tmp_code"
  elif [[ -n "$body" ]]; then
    curl -sS -X "$method" "$url" -H 'content-type: application/json' -d "$body" -o "$tmp_body" -w '%{http_code}' > "$tmp_code"
  elif [[ -n "$auth" ]]; then
    curl -sS -X "$method" "$url" -H "authorization: Bearer $auth" -o "$tmp_body" -w '%{http_code}' > "$tmp_code"
  else
    curl -sS -X "$method" "$url" -o "$tmp_body" -w '%{http_code}' > "$tmp_code"
  fi

  local code
  code=$(cat "$tmp_code")
  if [[ "$code" -lt 200 || "$code" -ge 300 ]]; then
    echo "Request failed ($method $url): HTTP $code"
    cat "$tmp_body"
    exit 1
  fi
  cat "$tmp_body"
}

echo "== Distributed AI-Enhanced Trading Platform Demo =="
echo

echo "1) Logging in as Alice..."
ALICE_LOGIN=$(call_json POST "$BASE_URL/auth/login" "{\"email\":\"$ALICE_EMAIL\",\"password\":\"$PASSWORD\"}")
ALICE_TOKEN=$(echo "$ALICE_LOGIN" | jq -r .access_token)
echo "   Alice authenticated."

echo "2) Logging in as Bob..."
BOB_LOGIN=$(call_json POST "$BASE_URL/auth/login" "{\"email\":\"$BOB_EMAIL\",\"password\":\"$PASSWORD\"}")
BOB_TOKEN=$(echo "$BOB_LOGIN" | jq -r .access_token)
echo "   Bob authenticated."

echo "3) Submitting BUY order for Alice..."
BUY=$(call_json POST "$BASE_URL/orders" "{\"account_id\":\"$ALICE_ACCOUNT_ID\",\"instrument_id\":\"$INSTRUMENT\",\"side\":\"BUY\",\"order_type\":\"LIMIT\",\"quantity\":$QTY,\"price\":$PRICE}" "$ALICE_TOKEN")
BUY_ID=$(echo "$BUY" | jq -r .id)
echo "   BUY order accepted for risk processing: $BUY_ID"

echo "4) Submitting SELL order for Bob..."
SELL=$(call_json POST "$BASE_URL/orders" "{\"account_id\":\"$BOB_ACCOUNT_ID\",\"instrument_id\":\"$INSTRUMENT\",\"side\":\"SELL\",\"order_type\":\"LIMIT\",\"quantity\":$QTY,\"price\":$PRICE}" "$BOB_TOKEN")
SELL_ID=$(echo "$SELL" | jq -r .id)
echo "   SELL order accepted for risk processing: $SELL_ID"

echo "5) Waiting for risk checks, matching, and portfolio updates..."
sleep 5

ALICE_PORTFOLIO=$(call_json GET "$BASE_URL/portfolio/$ALICE_ACCOUNT_ID" "" "$ALICE_TOKEN")
BOB_PORTFOLIO=$(call_json GET "$BASE_URL/portfolio/$BOB_ACCOUNT_ID" "" "$BOB_TOKEN")
ALICE_ACCOUNT=$(call_json GET "$BASE_URL/accounts/$ALICE_ACCOUNT_ID" "" "$ALICE_TOKEN")
BOB_ACCOUNT=$(call_json GET "$BASE_URL/accounts/$BOB_ACCOUNT_ID" "" "$BOB_TOKEN")
AUDIT=$(call_json GET "$BASE_URL/audit/events")

TRADE_COUNT=$(echo "$AUDIT" | jq '[.[] | select(.topic == "trades.executed.v1")] | length')
RISK_APPROVALS=$(echo "$AUDIT" | jq '[.[] | select(.topic == "risk.order.approved.v1")] | length')

if [[ "$RISK_APPROVALS" -ge 2 ]]; then
  echo "   Risk approved both orders."
else
  echo "Error: expected two risk approvals, saw $RISK_APPROVALS"
  exit 1
fi

if [[ "$TRADE_COUNT" -ge 1 ]]; then
  echo "   Trade executed."
else
  echo "Error: no execution event found in audit log"
  exit 1
fi

echo "   Portfolio updated."
echo

echo "6) Portfolio summary"
echo "   Alice position: $(echo "$ALICE_PORTFOLIO" | jq -r '.[0].quantity') $(echo "$ALICE_PORTFOLIO" | jq -r '.[0].instrument_id') @ avg $(echo "$ALICE_PORTFOLIO" | jq -r '.[0].avg_cost')"
echo "   Bob position:   $(echo "$BOB_PORTFOLIO" | jq -r '.[0].quantity') $(echo "$BOB_PORTFOLIO" | jq -r '.[0].instrument_id')"
echo "   Alice cash:     $(echo "$ALICE_ACCOUNT" | jq -r '.cash_balance')"
echo "   Bob cash:       $(echo "$BOB_ACCOUNT" | jq -r '.cash_balance')"
echo

echo "7) Audit summary"
echo "   Total audit events: $(echo "$AUDIT" | jq 'length')"
echo "   Trade events:       $TRADE_COUNT"
echo

echo "Demo complete: login -> buy -> sell -> risk approve -> match -> portfolio update"
