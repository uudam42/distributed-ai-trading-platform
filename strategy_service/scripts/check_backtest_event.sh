#!/usr/bin/env bash
set -euo pipefail
TOPIC="${1:-strategy.backtest.completed.v1}"
COUNT="${2:-1}"

docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic "$TOPIC" \
  --from-beginning \
  --max-messages "$COUNT"
