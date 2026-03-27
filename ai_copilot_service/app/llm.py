import json

import httpx

from .config import settings
from .logging_utils import configure_logging, log_kv
from .mock import mock_analysis

logger = configure_logging('ai-copilot-llm')


async def analyze_with_vllm(analysis_type: str, prompt: str, payload: dict) -> dict:
    if settings.ai_mock_mode:
        log_kv(logger, 'AICopilotLLM', 'mock_mode_active', analysis_type=analysis_type)
        return mock_analysis(analysis_type, payload)

    try:
        log_kv(logger, 'AICopilotLLM', 'prompt_send', analysis_type=analysis_type, prompt=prompt[:200])
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                f'{settings.vllm_base_url}/chat/completions',
                json={
                    'model': settings.vllm_model,
                    'messages': [
                        {'role': 'system', 'content': 'You are an AI trading copilot. Always return valid JSON only.'},
                        {'role': 'user', 'content': prompt},
                    ],
                    'temperature': 0.2,
                },
            )
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            log_kv(logger, 'AICopilotLLM', 'response_received', analysis_type=analysis_type)
            return json.loads(content)
    except Exception as exc:
        log_kv(logger, 'AICopilotLLM', 'fallback_to_mock', analysis_type=analysis_type, error=str(exc))
        return mock_analysis(analysis_type, payload)


async def healthcheck() -> dict:
    if settings.ai_mock_mode:
        return {'status': 'ok', 'mode': 'mock'}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f'{settings.vllm_base_url}/models')
            response.raise_for_status()
            return {'status': 'ok', 'mode': 'vllm'}
    except Exception as exc:
        return {'status': 'degraded', 'mode': 'fallback', 'error': str(exc)}
