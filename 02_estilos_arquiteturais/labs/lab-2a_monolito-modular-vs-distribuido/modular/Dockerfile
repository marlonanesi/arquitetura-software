FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /srv
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 "psycopg[binary]==3.2.3" import-linter==2.1
COPY app app
COPY .importlinter .
RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
