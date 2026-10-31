FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 "psycopg[binary]==3.2.3" httpx==0.28.1
COPY traducao.py legado.py novo.py gateway.py ./
EXPOSE 8000
# MODULO escolhe o serviço: legado, novo ou gateway
ENV MODULO=gateway
CMD ["sh", "-c", "uvicorn ${MODULO}:app --host 0.0.0.0 --port 8000"]
