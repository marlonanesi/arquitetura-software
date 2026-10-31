FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /srv
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 "psycopg[binary]==3.2.3" httpx==0.28.1
COPY app app
RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
# O mesmo código-base roda os três serviços; a variável SERVICO escolhe qual deles.
ENV SERVICO=entregas
CMD ["sh", "-c", "uvicorn app.${SERVICO}:app --host 0.0.0.0 --port 8000"]
