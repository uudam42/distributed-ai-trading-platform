# Architecture Overview

## Design Goals
- Low-latency order lifecycle for core trading paths
- Event-driven decoupling through Kafka
- Durable transactional record in PostgreSQL
- Hot-state caching and control-plane acceleration with Redis
- AI assistance separated from critical execution paths
- Tick-accurate strategy research with hftbacktest

## High-Level Components

```text
Clients / UI / Algo SDK
        |
        v
   API Gateway
        |
  -------------------------------
  |        |        |          |
  v        v        v          v
Auth    Order    Portfolio   Copilot APIs
          |
          v
       Kafka <---------------- Strategy Service
      /  |   \                      |
     /   |    \                     v
 Risk  Matching  Audit        hftbacktest Sim
   |       |
   |       v
   |    Trades/Fills --------> Portfolio
   |__________________________^
```

## Storage Allocation
- **PostgreSQL**
  - users, sessions, accounts
  - orders, fills, balances, positions
  - audit records
  - strategy definitions, backtest runs, simulation metadata
- **Redis**
  - risk limits and current exposure snapshots
  - latest order/portfolio views
  - session/JWT denylist or rate limiting buckets
  - order book snapshots / hot matching state mirror

## Reliability Patterns
- Transactional outbox per service for event publication consistency
- Idempotent consumers using event IDs and dedupe tables
- Schema versioning for Kafka payloads
- Dead-letter topics for poison messages
- Snapshot + replay for matching and portfolio rebuild

## Security Boundaries
- API Gateway validates and forwards only authenticated requests
- Auth Service owns identity and token issuance
- Matching Engine isolated from public network exposure
- AI Copilot is read-mostly and advisory by default
- Audit Service records access and administrative actions
