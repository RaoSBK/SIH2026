FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend_reqs.txt
COPY ml/requirements.txt ml_reqs.txt
RUN pip install --no-cache-dir -r backend_reqs.txt -r ml_reqs.txt

COPY backend /app/backend
COPY ml /app/ml

# Add /app to PYTHONPATH so backend can resolve absolute imports like `backend.app.main`
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
