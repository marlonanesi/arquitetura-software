FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir lizard==1.17.13
WORKDIR /scripts
# o repositório analisado fica em /dados (um volume) e os relatórios em /saida
RUN git config --global --add safe.directory '*'
