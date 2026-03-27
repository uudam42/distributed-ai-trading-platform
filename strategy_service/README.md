# Strategy Service

Isolated strategy research module for Phase 3.

## What it does
- loads historical tick/order-book style CSV data
- runs a simple imbalance-based strategy
- computes PnL, trade count, fill ratio, and inventory exposure
- writes a JSON report locally
- publishes `strategy.backtest.completed.v1` to Kafka

## Run locally

```bash
python strategy_service/run_backtest.py --dataset strategy_service/data/sample_ticks.csv
```

## Output
- JSON result to stdout
- JSON report file in `strategy_service/reports/`
- Kafka event on `strategy.backtest.completed.v1`

## Notes
- This module is intentionally isolated from the live trading path.
- TODO: extend to richer hftbacktest simulation wiring and additional strategies.
