FROM python:3.12-slim
WORKDIR /app
COPY app.py .
RUN useradd --system --uid 10001 app
USER 10001
CMD ["python", "app.py"]
