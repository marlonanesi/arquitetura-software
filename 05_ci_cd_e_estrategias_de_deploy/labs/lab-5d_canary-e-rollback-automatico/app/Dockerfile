FROM python:3.12-slim

ARG VERSAO=dev
ARG ERRO_PCT=0
ENV VERSAO=${VERSAO} ERRO_PCT=${ERRO_PCT} PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1
COPY main.py .

RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
