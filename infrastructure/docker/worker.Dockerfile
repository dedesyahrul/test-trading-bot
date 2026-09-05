FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# requirements.txt uses pinned versions, not hash-pinned requirements.
RUN PIP_REQUIRE_HASHES=0 PIP_CONFIG_FILE=/dev/null pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

CMD ["python", "-m", "arq", "app.workers.main.WorkerSettings"]
