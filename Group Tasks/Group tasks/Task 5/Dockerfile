FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_DATA_DIR=/data CHROMA_DB_PATH=/data/chroma_db HF_HOME=/data/models MODEL_CACHE_DIR=/data/models
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-task5.txt ./
RUN pip install --no-cache-dir -r requirements-task5.txt
COPY . .
RUN useradd --uid 10001 --create-home app && mkdir -p /data && chown -R app:app /data /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --start-period=120s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
