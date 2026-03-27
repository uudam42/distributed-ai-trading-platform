# Kafka Topics

## Domain Topics
- `auth.user.created.v1`
- `auth.login.succeeded.v1`
- `auth.login.failed.v1`
- `orders.received.v1`
- `orders.accepted.v1`
- `orders.rejected.v1`
- `orders.open.v1`
- `orders.partially_filled.v1`
- `orders.filled.v1`
- `orders.canceled.v1`
- `trades.executed.v1`
- `risk.order.approved.v1` (canonical)
- `risk.order.aproved.v1` (deprecated legacy compatibility topic)
- `risk.order.rejected.v1`
- `risk.limit.updated.v1`
- `risk.breach.detected.v1`
- `portfolio.position.updated.v1`
- `portfolio.balance.updated.v1`
- `portfolio.pnl.updated.v1`
- `strategy.registered.v1`
- `strategy.backtest.requested.v1`
- `strategy.backtest.completed.v1`
- `strategy.instance.started.v1`
- `strategy.instance.stopped.v1`
- `strategy.order_intents.v1`
- `audit.recorded.v1`
- `copilot.interaction.logged.v1`

## Infrastructure / Reliability Topics
- `dlq.orders.v1`
- `dlq.risk.v1`
- `dlq.matching.v1`
- `dlq.portfolio.v1`
- `dlq.strategy.v1`
- `dlq.copilot.v1`
- `snapshots.matching-engine.v1`
- `snapshots.portfolio.v1`

## Partitioning Guidance
- Orders and fills: partition by `account_id` or `instrument_id` depending on matching topology
- Risk: partition by `account_id`
- Portfolio: partition by `account_id`
- Strategy events: partition by `strategy_id`
- Audit: partition by event date or tenant for throughput
