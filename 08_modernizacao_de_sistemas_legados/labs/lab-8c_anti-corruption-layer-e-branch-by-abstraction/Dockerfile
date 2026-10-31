FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 httpx==0.28.1 pytest==8.3.4
COPY legado legado
COPY novo novo
COPY tests tests
COPY pytest.ini .
