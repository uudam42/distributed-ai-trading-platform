FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app
COPY ai_copilot_service /app/ai_copilot_service
RUN pip install --no-cache-dir -r /app/ai_copilot_service/requirements.txt
CMD ["uvicorn", "ai_copilot_service.app.main:app", "--host", "0.0.0.0", "--port", "8091"]
