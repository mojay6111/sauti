FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ml/requirements.txt ./ml/requirements.txt
RUN pip install --no-cache-dir -r ml/requirements.txt

COPY ml/ ./ml/
COPY data/schemas/ ./data/schemas/
COPY annotation/seed_examples/ ./annotation/seed_examples/

RUN mkdir -p ml/runs data/raw data/processed data/annotated data/feedback

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "ml.src.training.train"]
