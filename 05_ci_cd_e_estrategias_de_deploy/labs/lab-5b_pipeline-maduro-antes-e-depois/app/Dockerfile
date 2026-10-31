FROM python:3.12-slim

ARG VERSAO=dev
ENV VERSAO=${VERSAO} PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --retries=5 CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/saude')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
