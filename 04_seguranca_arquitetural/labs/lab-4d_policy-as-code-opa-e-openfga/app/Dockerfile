FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 httpx==0.28.1
COPY servico.py .
COPY catalogos catalogos
RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "servico:app", "--host", "0.0.0.0", "--port", "8000"]
