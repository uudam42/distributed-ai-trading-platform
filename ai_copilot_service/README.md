# AI Copilot Service

Phase 4 / 4.1 async AI analysis module.

## Features
- explain rejected orders
- summarize backtest results
- answer portfolio risk questions
- consume `ai.analysis.request.v1`
- produce `ai.analysis.result.v1`
- synchronous test endpoint: `POST /analyze`
- `GET /health/ai` for validation
- deterministic mock mode via `AI_MOCK_MODE=true`

## Mock mode

Run with mock mode when vLLM is unavailable:

```bash
AI_MOCK_MODE=true docker compose --profile ai up --build -d ai-copilot-service
```

## Real vLLM mode

```bash
docker compose --profile ai up --build -d ai-copilot-service vllm
```

## Example request

```json
{
  "analysis_type": "strategy_summary",
  "payload": {
    "strategy": "mean_reversion",
    "pnl": 0.1,
    "trades": 3,
    "fill_ratio": 0.6,
    "inventory_exposure": 0.8
  }
}
```

## Kafka test flow

```bash
bash ai_copilot_service/scripts/test_kafka_flow.sh
```

## Example response shape

```json
{
  "event_id": "...",
  "analysis_type": "strategy_summary",
  "result": {
    "summary": "...",
    "strengths": ["..."],
    "weaknesses": ["..."],
    "follow_ups": ["..."]
  },
  "timestamp": "..."
}
```
