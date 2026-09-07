FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2 and others
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install both backend and ML dependencies
COPY backend/requirements.txt backend_reqs.txt
COPY ml/requirements.txt ml_reqs.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r backend_reqs.txt -r ml_reqs.txt

# Copy application code
COPY backend /app/backend
COPY ml /app/ml
COPY cias_er /app/cias_er

# Add /app to PYTHONPATH so backend can resolve absolute imports
ENV PYTHONPATH=/app:/app/backend

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
