FROM python:3.12-slim

ARG VERSAO=1.0.0
ENV VERSAO=${VERSAO} PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

# Roda sem privilégios. A imagem não muda entre ambientes: só a configuração muda.
RUN useradd --system --uid 10001 app
USER 10001

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
