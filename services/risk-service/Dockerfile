FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app:/app/shared
COPY shared /app/shared
COPY services/risk-service /app/service
RUN pip install --no-cache-dir -r /app/service/requirements.txt
CMD ["uvicorn", "service.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
