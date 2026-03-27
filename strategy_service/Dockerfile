FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app
COPY strategy_service /app/strategy_service
RUN pip install --no-cache-dir -r /app/strategy_service/requirements.txt
CMD ["python", "strategy_service/run_backtest.py", "--dataset", "strategy_service/data/sample_ticks.csv"]
