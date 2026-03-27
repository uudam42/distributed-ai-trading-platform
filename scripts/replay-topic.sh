#!/usr/bin/env bash
set -euo pipefail

TOPIC="${1:-}"
GROUP="${2:-replay-debugger}"
RESET="${3:-}"

if [[ -z "$TOPIC" ]]; then
  echo "Usage: $0 <topic> [consumer-group] [--reset]"
  exit 1
fi

if [[ "$RESET" == "--reset" ]]; then
  echo "[Replay] resetting offsets for group=$GROUP topic=$TOPIC"
  docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
    --bootstrap-server kafka:9092 \
    --group "$GROUP" \
    --topic "$TOPIC" \
    --reset-offsets --to-earliest --execute
fi

echo "[Replay] consuming topic=$TOPIC group=$GROUP from earliest"
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic "$TOPIC" \
  --group "$GROUP" \
  --from-beginning
