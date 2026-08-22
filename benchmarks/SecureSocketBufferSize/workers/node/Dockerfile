FROM node:24-bookworm-slim
WORKDIR /app
COPY workers/node/benchmark.js /app/benchmark.js
COPY certs /app/certs
ENTRYPOINT ["node", "/app/benchmark.js"]
