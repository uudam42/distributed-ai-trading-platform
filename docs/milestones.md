# Implementation Milestones

## Milestone 0 — Monorepo and Platform Bootstrap
- Create repo structure and base docs
- Add Docker Compose for PostgreSQL, Redis, Kafka, and all services
- Add `.env.example`
- Add health endpoints and placeholder Dockerfiles for every service
- Define initial OpenAPI specs and Kafka topic catalog

## Milestone 1 — Identity, Gateway, and Order Intake
- Implement Auth Service JWT flows and API key support
- Implement API Gateway auth middleware, routing, and rate limiting
- Implement Order Service create/get/cancel APIs
- Add PostgreSQL schemas and transactional outbox
- Demo: authenticated client can place and query an order

## Milestone 2 — Risk Controls and Matching Core
- Implement Risk Service pre-trade checks and limit configs
- Implement Matching Engine in-memory order book with Kafka consumers/producers
- Wire order approval/rejection and execution lifecycle
- Add Redis hot-state for exposures and active books
- Demo: approved orders match and emit fills end-to-end

## Milestone 3 — Portfolio and Audit Read Models
- Implement Portfolio Service position/balance/PnL projections
- Implement Audit Service append-only event archive and query APIs
- Add replay/rebuild tooling for projections
- Demo: executions update account portfolio and are auditable

## Milestone 4 — Strategy Research and Simulation
- Integrate hftbacktest into Strategy Service
- Add backtest job orchestration, parameter sweeps, and result persistence
- Support paper trading loop consuming live market/order events
- Demo: run tick-level backtest and compare with paper strategy outputs

## Milestone 5 — AI Copilot and Operator Workflows
- Integrate vLLM OpenAI-compatible client in AI Copilot Service
- Add portfolio/risk/order explanation endpoints
- Add retrieval over internal docs, audit summaries, and strategy reports
- Guardrails: advisory-only default, action proposals require explicit confirmation
- Demo: copilot explains a fill, summarizes account risk, and suggests strategy tuning ideas

## Milestone 6 — Production Hardening
- Add observability: Prometheus, Grafana, OpenTelemetry, tracing
- Add schema registry / protobuf or Avro contracts
- Add HA considerations, partitioning, snapshot/replay, and backpressure controls
- Add chaos/failure testing and disaster recovery runbooks
- Add CI/CD, security scans, and performance benchmarks
