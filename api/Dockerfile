FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY api/requirements_slim.txt ./api/requirements_slim.txt
RUN pip install --no-cache-dir -r api/requirements_slim.txt

COPY ml/ ./ml/
COPY api/ ./api/
COPY data/schemas/ ./data/schemas/
COPY annotation/seed_examples/ ./annotation/seed_examples/
COPY data/annotated/ ./data/annotated/

RUN mkdir -p ml/runs data/feedback

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENV=production

EXPOSE 8000

CMD ["uvicorn", "api.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
