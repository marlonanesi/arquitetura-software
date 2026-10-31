FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /lab
RUN pip install --no-cache-dir pytest==8.3.4 "psycopg[binary]==3.2.3"
COPY pytest.ini .
COPY src src
COPY tests tests
COPY extras extras
ENV PYTHONPATH=/lab/src
CMD ["python", "-m", "confirmacao.cli", "demo"]
