FROM alpine:3.21
WORKDIR /app
COPY workers/observer/snapshot.sh /app/snapshot.sh
RUN chmod +x /app/snapshot.sh
ENTRYPOINT ["sh", "-c", "trap 'exit 0' TERM INT; while :; do sleep 3600 & wait $!; done"]
