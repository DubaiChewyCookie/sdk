# Secure socket buffer size benchmark

This bounded benchmark measures the TLS/plaintext coefficient of Dart,
Node.js, and Go over persistent `io` and HTTP/1.1 keep-alive paths. Payloads
are 1 KiB, 16 KiB, 64 KiB, and 1 MiB.

Each runtime is measured separately in both endpoint roles:

- target server: the target gets one physical core; a fixed Go client gets
  four physical cores;
- target client: the target gets one physical core; a fixed Go server gets
  four physical cores.

Each endpoint runs in a separate Linux container. The client shares the
server's network namespace so traffic stays on kernel loopback. Docker cpusets
select one logical CPU from each physical core and exclude SMT siblings;
`--cpus` also enforces the one-versus-four CPU count. The target, partner, and
cgroup observer use disjoint cpusets. Every endpoint has a generous 4 GiB
memory limit with swap disabled.

The observer records target and partner cgroup user/system CPU time, CPU per
operation, memory, and throttling separately. QPS and round-trip
mean/p50/p95/p99 latency are produced by the client. Handshake, connection
creation, image build, and warmup occur before the measurement barrier.

Dart TLS is measured at secure socket buffer sizes 8, 32, 128, and 512 KiB and
1 MiB for the 1 MiB payload. The default quick suite uses two repetitions and
448 cells. It is designed as a short PR diagnostic, not a maximum-tuned
production benchmark.

## Prerequisites

- Docker Desktop on Windows/macOS or a BuildKit-enabled Docker Engine on Linux,
  with at least six visible physical cores and 10 GiB of available memory for
  Linux containers;
- Python 3 with `psutil` and OpenSSL;
- the checked-out SDK branch with its dependencies fetched.

The Dart worker image builds a native ReleaseX64 or ReleaseARM64 SDK from the
checked-out branch source. Go and Node.js run from their own multi-architecture
worker images. AMD64 and ARM64 results describe different host architectures
and must not be compared directly.

## Commands

On Windows PowerShell:

```powershell
cd benchmarks\SecureSocketBufferSize
python -m pip install -r requirements.txt
.\run.ps1 prepare
.\run.ps1 smoke --run-id smoke-local
.\run.ps1 quick --run-id quick-local
.\run.ps1 retry --run-id quick-local
.\run.ps1 report --run-id quick-local
```

On Linux or macOS:

```bash
cd benchmarks/SecureSocketBufferSize
python3 -m pip install -r requirements.txt
bash ./run.sh prepare
bash ./run.sh smoke --run-id smoke-local
bash ./run.sh quick --run-id quick-local
bash ./run.sh retry --run-id quick-local
bash ./run.sh report --run-id quick-local
```

`run.sh` uses `python3` by default. Set `PYTHON` to select another Python 3
executable.

Useful bounded overrides are `--repetitions`, `--warmup-ms`,
`--throughput-ms`, and `--latency-ms`.

Each run writes `REPORT.md`, `summary.csv`, `cell_results.csv`, environment and
image provenance, the physical-core placement, cgroup snapshots, and endpoint
logs under `results/<run-id>/`.
