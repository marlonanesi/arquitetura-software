FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /srv
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 "psycopg[binary]==3.2.3" PyJWT==2.10.1
COPY inseguro/main.py inseguro_main.py
COPY seguro/main.py seguro_main.py
RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
# MODO escolhe qual das duas versões roda: inseguro ou seguro
ENV MODO=inseguro
CMD ["sh", "-c", "uvicorn ${MODO}_main:app --host 0.0.0.0 --port 8000"]
