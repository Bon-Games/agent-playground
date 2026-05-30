FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    anthropic \
    schedule \
    python-dotenv \
    requests
ENV PYTHONPATH=/app/workflows
CMD ["python", "/app/workflows/scheduler-service.py"]
