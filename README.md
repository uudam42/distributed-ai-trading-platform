# Distributed AI-Enhanced Trading Platform

A demo-ready distributed trading platform built as a service-oriented monorepo. It demonstrates an end-to-end order lifecycle using FastAPI services, Kafka for event propagation, PostgreSQL for durable state, and Docker Compose for local orchestration.

The current platform is intentionally scoped to a clean production-style Phase 1 / 1.5 slice: authentication, order intake, risk approval, matching, execution publication, portfolio updates, and auditable event history. It is designed to look and behave like a real distributed trading system while keeping the implementation minimal and understandable.

## System Architecture

```text
                External Client
                      |
                      v
               API Gateway :8090
          /auth  /orders  /portfolio  /audit
                      |
        -------------------------------------------
        |              |             |            |
        v              v             v            v
   Auth Service   Order Service  Portfolio    Audit Service
                         |
                         v
                 orders.received.v1
                         |
                         v
                    Risk Service
                         |
              risk.order.approved.v1
                         |
                         v
                  orders.accepted.v1
                         |
                         v
                 Matching Engine
                         |
                   trades.executed.v1
                         |
                         v
                  Portfolio Service

Shared infrastructure:
- PostgreSQL for users, accounts, orders, trades, positions, audit events
- Kafka for service-to-service event propagation
```

## Event Flow

1. Client logs in through the API Gateway.
2. API Gateway routes `/auth/*` requests to Auth Service.
3. Client submits a limit order through `/orders`.
4. Order Service persists the order and emits `orders.received.v1`.
5. Risk Service consumes the event and approves or rejects it.
6. Approved orders are emitted on `orders.accepted.v1`.
7. Matching Engine applies price-time priority and emits `trades.executed.v1` when a match occurs.
8. Portfolio Service consumes the trade event and updates balances and positions.
9. Audit Service exposes the event trail for inspection.

## Why Kafka

Kafka provides a clean event backbone between services. It decouples order intake, risk checks, matching, and portfolio projection so each service can own a small part of the workflow while remaining independently replaceable. For this project, Kafka makes the system look and behave like a real distributed trading platform instead of a single-process demo.

## Service Responsibilities

- **API Gateway**
  - single external entry point on port `8090`
  - request routing to internal services
  - request logging middleware

- **Auth Service**
  - user login
  - JWT issuance
  - seed-user authentication

- **Order Service**
  - order creation and retrieval
  - persistence of submitted orders
  - publication of `orders.received.v1`

- **Risk Service**
  - minimal pre-trade checks
  - approval/rejection events
  - publication of `orders.accepted.v1`

- **Matching Engine**
  - in-memory order book
  - price-time-priority matching
  - publication of `trades.executed.v1`

- **Portfolio Service**
  - position and cash balance updates from executed trades
  - portfolio/account read APIs

- **Audit Service**
  - queryable audit/event log for demo visibility

## How to Run

```bash
make build
make up
make demo
```

Gateway entrypoint:
- `http://localhost:8090`

Seed credentials:
- `alice@example.com / password123`
- `bob@example.com / password123`

## Example Demo Output

```text
== Distributed AI-Enhanced Trading Platform Demo ==

1) Logging in as Alice...
   Alice authenticated.
2) Logging in as Bob...
   Bob authenticated.
3) Submitting BUY order for Alice...
   BUY order accepted for risk processing: <order-id>
4) Submitting SELL order for Bob...
   SELL order accepted for risk processing: <order-id>
5) Waiting for risk checks, matching, and portfolio updates...
   Risk approved both orders.
   Trade executed.
   Portfolio updated.
6) Portfolio summary
   Alice position: 1.0 BTC-USD @ avg 100.0
   Bob position:   -1.0 BTC-USD
   Alice cash:     99900.0
   Bob cash:       100100.0
7) Audit summary
   Total audit events: 10
   Trade events:       1
```

## Phase Breakdown

### Phase 1 — Done
- runnable FastAPI services for auth, order, risk, matching, portfolio, and audit
- Kafka-based event flow for the happy path
- PostgreSQL persistence and seed data
- working end-to-end trade lifecycle

### Phase 1.5 — Done
- gateway-only external access on port `8090`
- cleaner compose and health checks
- gateway request logging
- structured service logs
- gateway-only demo flow
- professional README and presentation cleanup

### Phase 2 — Kafka Event-Driven Hardening
- Kafka-only service communication for the trading path
- consumer-side schema validation
- retry handling with retry limits
- dead letter queues using `<topic>.dlq`
- idempotency protection for duplicate execution and portfolio updates
- clearer consumer loop structure and replay/debug support

### Phase 2.1 — Hardening Polish
- PostgreSQL-backed idempotency tracking that survives restarts
- DLQ inspection endpoints exposed through the gateway
- replay helper script for Kafka topics and optional consumer group offset reset
- corrected topic naming: canonical = `risk.order.approved.v1`; deprecated legacy compatibility = `risk.order.aproved.v1`
- clearer logging for retries, DLQ routing, idempotency skips, and replay operations

Replay usage:
```bash
bash scripts/replay-topic.sh <topic> [consumer-group] [--reset]
```

### Future Phase 3
- richer risk controls
- cancel/amend flows
- stronger auth model
- transactional outbox / delivery hardening
- Redis hot-state cache

### Phase 3 — Strategy Research Module
- isolated `strategy_service` module added outside the live trading path
- simple research strategies over historical tick/order-book style CSV data
- strategies included:
  - `imbalance`
  - `mean_reversion`
- backtest metrics: PnL, trade count, fill ratio, inventory exposure
- local JSON reports written to `strategy_service/reports/`
- optional CSV export
- Kafka publication on `strategy.backtest.completed.v1`
- standalone CLI runner:
  ```bash
  KAFKA_BOOTSTRAP_SERVERS=localhost:9092 python strategy_service/run_backtest.py --dataset strategy_service/data/sample_ticks.csv --strategy imbalance --csv
  ```
- Dockerized runner in the Compose network:
  ```bash
  docker compose --profile strategy run --rm strategy-runner python strategy_service/run_backtest.py --dataset strategy_service/data/sample_ticks.csv --strategy mean_reversion --csv
  ```
- event verification:
  ```bash
  bash strategy_service/scripts/check_backtest_event.sh strategy.backtest.completed.v1 1
  ```

### Future Phase 4
- lower-latency matching replacement path
- broader market simulation
- richer hftbacktest wiring and additional strategies

### Phase 4 — AI Copilot Integration
- isolated `ai_copilot_service` added with FastAPI
- connects to a vLLM OpenAI-compatible endpoint
- supports:
  - rejected order explanation
  - backtest result summary
  - portfolio risk Q&A
- Kafka async flow:
  - consumes `ai.analysis.request.v1`
  - produces `ai.analysis.result.v1`
- test endpoint:
  ```bash
  curl -X POST http://localhost:8091/analyze -H 'content-type: application/json' -d '{"analysis_type":"strategy_summary","payload":{"strategy":"mean_reversion","pnl":0.1,"trades":3,"fill_ratio":0.6,"inventory_exposure":0.8}}'
  ```
- outputs are structured JSON

### Phase 4.1 — AI Validation and Testing
- deterministic mock mode via `AI_MOCK_MODE=true`
- timeout + fallback to mock if vLLM is unavailable
- validation endpoint:
  ```bash
  curl http://localhost:8091/health/ai
  ```
- Kafka end-to-end test:
  ```bash
  bash ai_copilot_service/scripts/test_kafka_flow.sh
  ```
- mock mode run:
  ```bash
  AI_MOCK_MODE=true docker compose --profile ai up --build -d ai-copilot-service
  ```
- real vLLM mode run:
  ```bash
  docker compose --profile ai up --build -d ai-copilot-service vllm
  ```

### Future Phase 5
- observability and operational tooling

## Deferred Features

Not part of Phase 1 / 1.5:
- hftbacktest integration
- vLLM integration
- strategy runtime
- AI copilot runtime
- Redis hot-state acceleration
- performance optimization beyond cleanup
