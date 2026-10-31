FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 "psycopg[binary]==3.2.3" pytest==8.3.4
COPY src src
COPY tests tests
COPY pytest.ini .
CMD ["uvicorn", "api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
