FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lunalog ./lunalog
ENV PYTHONUNBUFFERED=1

RUN useradd --system --uid 10001 app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "lunalog.api.rotas:app", "--host", "0.0.0.0", "--port", "8000"]
