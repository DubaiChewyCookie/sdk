# syntax=docker/dockerfile:1.7
FROM golang:1.25-bookworm AS build
WORKDIR /src
COPY workers/go/go.mod workers/go/go.sum ./
RUN go mod download
COPY workers/go/ ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /out/benchmark-worker ./cmd/benchmark \
    && go version > /out/runtime-version.txt

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /out/benchmark-worker /app/benchmark-worker
COPY --from=build /out/runtime-version.txt /app/runtime-version.txt
COPY certs /app/certs
ENTRYPOINT ["/app/benchmark-worker"]
