#!/usr/bin/env bash
set -euo pipefail

BROKER="${KAFKA_BROKERS:-kafka:9092}"
TOPICS=(
  auth.user.created.v1
  auth.login.succeeded.v1
  auth.login.failed.v1
  orders.received.v1
  orders.accepted.v1
  orders.rejected.v1
  orders.open.v1
  orders.partially_filled.v1
  orders.filled.v1
  orders.canceled.v1
  trades.executed.v1
  risk.order.approved.v1
  risk.order.rejected.v1
  risk.limit.updated.v1
  risk.breach.detected.v1
  portfolio.position.updated.v1
  portfolio.balance.updated.v1
  portfolio.pnl.updated.v1
  strategy.registered.v1
  strategy.backtest.requested.v1
  strategy.backtest.completed.v1
  strategy.instance.started.v1
  strategy.instance.stopped.v1
  strategy.order_intents.v1
  audit.recorded.v1
  copilot.interaction.logged.v1
)

for topic in "${TOPICS[@]}"; do
  /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server "$BROKER" \
    --create --if-not-exists \
    --topic "$topic" \
    --replication-factor 1 \
    --partitions 3
done
