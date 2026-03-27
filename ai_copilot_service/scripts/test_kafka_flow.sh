#!/usr/bin/env bash
set -euo pipefail

REQ_TOPIC="ai.analysis.request.v1"
RES_TOPIC="ai.analysis.result.v1"

REQUEST='{"analysis_type":"strategy_summary","payload":{"strategy":"mean_reversion","pnl":0.1,"trades":3,"fill_ratio":0.6,"inventory_exposure":0.8}}'

echo "[AI Test] producing request to $REQ_TOPIC"
docker compose exec kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic "$REQ_TOPIC" <<< "$REQUEST"

echo "[AI Test] consuming one response from $RES_TOPIC"
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic "$RES_TOPIC" --from-beginning --max-messages 1
