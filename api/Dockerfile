FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ML deps needed because API loads model directly
COPY ml/requirements.txt ./ml/requirements.txt
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r ml/requirements.txt -r api/requirements.txt

# Source
COPY ml/ ./ml/
COPY api/ ./api/
COPY data/schemas/ ./data/schemas/
COPY annotation/seed_examples/ ./annotation/seed_examples/

RUN mkdir -p ml/runs data/feedback

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENV=production

EXPOSE 8000

CMD ["uvicorn", "api.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
