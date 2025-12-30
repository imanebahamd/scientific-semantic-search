FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=1000 --retries 5 -r requirements.txt

COPY . .

RUN mkdir -p /app/data/raw /app/data/cleaned /app/data/enhanced

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.routes_simple:api", "--host", "0.0.0.0", "--port", "8000", "--reload"]
