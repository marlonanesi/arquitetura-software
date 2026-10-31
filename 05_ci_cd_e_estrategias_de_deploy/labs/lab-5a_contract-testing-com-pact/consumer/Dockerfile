FROM node:20-bookworm-slim

WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY src ./src
COPY test ./test
COPY scripts ./scripts
