import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from shared.app.config import settings
from shared.app.logging_utils import RequestTimer, configure_logging, log_kv
from shared.app.schemas import HealthResponse

app = FastAPI(title='API Gateway')
logger = configure_logging('api-gateway')

ROUTES = {
    'auth': settings.auth_service_url,
    'orders': settings.order_service_url,
    'portfolio': settings.portfolio_service_url,
    'audit': 'http://audit-service:8086',
}


@app.middleware('http')
async def request_logging(request: Request, call_next):
    timer = RequestTimer()
    response = await call_next(request)
    log_kv(
        logger,
        'APIGateway',
        'request',
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=f'{timer.ms:.2f}',
    )
    return response


@app.get('/health', response_model=HealthResponse)
def health():
    return HealthResponse(status='ok', service=settings.service_name)


async def proxy(service_key: str, path: str, request: Request) -> Response:
    base_url = ROUTES[service_key]
    target = f'{base_url}/{path}' if path else base_url
    headers = {k: v for k, v in request.headers.items() if k.lower() in {'authorization', 'content-type'}}
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(request.method, target, content=body or None, headers=headers, params=request.query_params)
    content_type = resp.headers.get('content-type', '')
    if 'application/json' in content_type:
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    return Response(status_code=resp.status_code, content=resp.content, media_type=content_type or None)


@app.api_route('/auth/{path:path}', methods=['GET', 'POST'])
async def auth_proxy(path: str, request: Request):
    return await proxy('auth', f'auth/{path}', request)


@app.api_route('/orders', methods=['GET', 'POST'])
async def orders_root(request: Request):
    return await proxy('orders', 'orders', request)


@app.api_route('/orders/{path:path}', methods=['GET', 'POST'])
async def orders_proxy(path: str, request: Request):
    return await proxy('orders', f'orders/{path}', request)


@app.api_route('/portfolio/{path:path}', methods=['GET'])
async def portfolio_proxy(path: str, request: Request):
    return await proxy('portfolio', f'portfolio/{path}', request)


@app.api_route('/accounts/{path:path}', methods=['GET'])
async def accounts_proxy(path: str, request: Request):
    return await proxy('portfolio', f'accounts/{path}', request)


@app.api_route('/audit/{path:path}', methods=['GET'])
async def audit_proxy(path: str, request: Request):
    return await proxy('audit', f'audit/{path}', request)
