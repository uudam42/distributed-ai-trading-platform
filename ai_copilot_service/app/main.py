from datetime import datetime

from fastapi import FastAPI

from .kafka import publish, start_consumer, start_producer, stop_consumer, stop_producer
from .llm import analyze_with_vllm, healthcheck
from .logging_utils import configure_logging, log_kv
from .prompts import PROMPTS
from .schemas import AnalyzeRequest, AnalyzeResult

app = FastAPI(title='AI Copilot Service')
logger = configure_logging('ai-copilot-service')


async def run_analysis(request: AnalyzeRequest) -> AnalyzeResult:
    prompt = PROMPTS[request.analysis_type].format(payload=request.payload)
    log_kv(logger, 'AICopilotService', 'incoming_request', analysis_type=request.analysis_type, event_id=request.event_id)
    result = await analyze_with_vllm(request.analysis_type, prompt, request.payload)
    output = AnalyzeResult(
        event_id=request.event_id,
        analysis_type=request.analysis_type,
        result=result,
        timestamp=datetime.utcnow(),
    )
    await publish('ai.analysis.result.v1', output.model_dump(mode='json'), key=str(output.event_id))
    log_kv(logger, 'AICopilotService', 'analysis_complete', analysis_type=request.analysis_type, event_id=request.event_id)
    return output


async def handle_kafka_request(payload: dict):
    request = AnalyzeRequest.model_validate(payload)
    await run_analysis(request)


@app.on_event('startup')
async def startup():
    await start_producer()
    await start_consumer(handle_kafka_request)


@app.on_event('shutdown')
async def shutdown():
    await stop_consumer()
    await stop_producer()


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'ai-copilot-service'}


@app.get('/health/ai')
async def health_ai():
    return await healthcheck()


@app.post('/analyze')
async def analyze(request: AnalyzeRequest):
    output = await run_analysis(request)
    return output.model_dump(mode='json')
