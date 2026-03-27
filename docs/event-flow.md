# Event Flow

## Primary Order Lifecycle

1. `POST /api/v1/orders` hits API Gateway
2. API Gateway forwards to Order Service with user/account claims
3. Order Service writes order row with status `PENDING_RISK`
4. Order Service emits `orders.received.v1`
5. Risk Service consumes event, loads current exposures from Redis/PostgreSQL
6. Risk Service emits either:
   - `risk.order.approved.v1` (canonical; legacy compatibility accepts `risk.order.aproved.v1` temporarily)
   - `risk.order.rejected.v1`
7. On approval, Order Service updates status to `ACCEPTED` and emits `orders.accepted.v1`
8. Matching Engine consumes accepted order and matches against book
9. Matching Engine emits:
   - `orders.open.v1`
   - `orders.partially_filled.v1`
   - `orders.filled.v1`
   - `orders.canceled.v1`
   - `trades.executed.v1`
10. Portfolio Service consumes execution events and updates positions, balances, PnL
11. Audit Service consumes the full stream and persists append-only audit records

## Strategy Lifecycle

1. Quant uploads strategy config/code package metadata
2. Strategy Service stores strategy definition and emits `strategy.registered.v1`
3. Strategy backtest request triggers hftbacktest run
4. Results are persisted and emitted as `strategy.backtest.completed.v1`
5. Live strategy instances emit `strategy.order_intents.v1`
6. Order Service transforms those intents into normal order workflow entries

## AI Copilot Flow

1. User asks a question via Gateway to AI Copilot Service
2. Copilot pulls curated state from Portfolio/Risk/Audit read models
3. Copilot calls vLLM OpenAI-compatible endpoint
4. Copilot returns explanation, summary, or suggested action
5. If suggestions are persisted, emit `copilot.interaction.logged.v1`
