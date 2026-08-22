# syntax=docker/dockerfile:1.7
FROM debian:bookworm-slim AS sdk-build
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git python3 xz-utils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY . .
RUN curl -fsSL 'https://chrome-infra-packages.appspot.com/client?platform=linux-amd64&version=git_revision:2947bd98a9c59d4f552df3a043c5883651448e0a' \
      -o /usr/local/bin/cipd \
    && chmod +x /usr/local/bin/cipd \
    && cipd install gn/gn/linux-amd64 \
      git_revision:e8a8e0932a5e42a99e5896aa58e3b8290f4e5b8c -root /tmp/gn \
    && cipd install infra/3pp/tools/ninja/linux-amd64 \
      'version:3@1.13.2.chromium.4' -root /tmp/ninja \
    && cipd install fuchsia/third_party/sysroot/linux \
      git_revision:fa7a5a9710540f30ff98ae48b62f2cdf72ed2acd \
      -root /tmp/sysroot \
    && cipd install dart/dart-sdk/linux-amd64 \
      'version:3.14.0-75.0.dev' -root /tmp/bootstrap-sdk \
    && cp /tmp/gn/gn /src/buildtools/gn \
    && cp /tmp/ninja/ninja /src/buildtools/ninja/ninja \
    && mkdir -p /src/buildtools/sysroot/linux \
    && cp -a /tmp/sysroot/. /src/buildtools/sysroot/linux/ \
    && rm -rf /src/tools/sdks/dart-sdk \
    && cp -a /tmp/bootstrap-sdk /src/tools/sdks/dart-sdk
RUN find build runtime sdk tools utils -type f \
      \( -name '*.py' -o -name '*.sh' \) -exec sed -i 's/\r$//' {} +
RUN python3 tools/generate_package_config.py
RUN python3 tools/build.py -m release -a x64 create_sdk
WORKDIR /src/benchmarks/SecureSocketBufferSize/workers/dart
RUN mkdir -p /out \
    && /src/out/ReleaseX64/dart-sdk/bin/dart pub get \
    && /src/out/ReleaseX64/dart-sdk/bin/dart analyze \
    && /src/out/ReleaseX64/dart-sdk/bin/dart compile exe bin/benchmark.dart -o /out/benchmark-worker \
    && /src/out/ReleaseX64/dart-sdk/bin/dart --version > /out/runtime-version.txt 2>&1

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=sdk-build /out/benchmark-worker /app/benchmark-worker
COPY --from=sdk-build /out/runtime-version.txt /app/runtime-version.txt
COPY benchmarks/SecureSocketBufferSize/certs /app/certs
ENTRYPOINT ["/app/benchmark-worker"]
