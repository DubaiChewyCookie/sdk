# Secure socket buffer size benchmark report

## Benchmark setup

**Full values:** [all benchmark data](FULL_RESULTS.md#full-benchmark-results)

| Item | Value |
|---|---|
| Run | `quick-isolated-20260823`; quick; 3 repetitions; 162.4 min |
| Timing | warmup 3000 ms; throughput 12000 ms; latency 8000 ms |
| Workload | persistent `io` echo and HTTP/1.1 keep-alive; throughput window 8; latency window 1 |
| CPU placement | target 1 core; fixed Go partner 4 cores; observer 1 core |
| Network | separate Linux containers; shared network namespace; loopback |
| Memory | 4 GiB per container; swap disabled |
| Runtimes | Dart: `Dart SDK version: 3.14.0-edge.None (main) (Unknown timestamp) on "linux_x64"`; Node.js: `v24.19.0`; Go: `go version go1.25.14 linux/amd64` |
| Source | SDK `1a6c95741dbe5d6140970f690d22f22f2834a39f` |
| Docker CPUs | 16 physical / 32 logical; LLC `inferred_5950x_core_halves_due_wsl` |
| Validity | 672/672 cells; max QPS CV 37.8%; CV ≥10% in 4 groups |
| Cgroup limits | target throttled in 123 cells (max 28 periods); partner max CPU 53.7% of 4 cores; partner throttled in 0 cells |

<details>
<summary>Throughput groups with QPS CV ≥10%</summary>

**Full values:** [QPS and variability](FULL_RESULTS.md#absolute-8-kib-qps)

| Target | Role | Path | TLS | Payload | QPS range | CV |
|---|---|---|---:|---:|---:|---:|
| Go | server | io | yes | 1 MiB | 325–685 | 37.8% |
| Node | client | http | no | 64 KiB | 6,225–9,449 | 17.7% |
| Go | client | io | no | 1 MiB | 4,012–5,487 | 13.8% |
| Node | server | io | no | 1 MiB | 1,230–1,651 | 11.9% |

</details>

## How to read this report

**Fairness controls:** role symmetry · fixed Go partner · pinned physical cores · no SMT siblings · partner headroom · isolated observer · identical loopback · fixed container limits · warmup barrier · deterministic order · repeated medians.

Absolute results can still reflect differences between runtimes' I/O and HTTP implementations, as well as asymmetries in the benchmark harness. The main report therefore emphasizes TLS/plaintext coefficients instead of cross-runtime absolute values.

Each coefficient compares a runtime with itself while holding the language, role, path, payload, window, and 8 KiB buffer constant; only TLS versus plaintext changes. This self-comparison cancels runtime implementation differences and benchmark-harness unfairness from the coefficient itself. See the [full absolute results](FULL_RESULTS.md) when absolute values are needed.

## Finding: counterintuitive Dart TLS metrics at 8 KiB

Each unidirectional Dart TLS transfer traverses three of six buffers: four Dart native shared buffers (plain and encrypted, two each) and two BoringSSL BIO buffers. The TLS/plain coefficients below make the resulting allocation and copy pressure visible against the Node.js and Go baselines; `1.00×` is the corresponding plain-socket result.

### QPS

At 1 MiB, Dart TLS retains only **0.04–0.11×** of plain QPS, versus 0.33–0.61× for Node.js and 0.08–0.48× for Go. The **0.04× server/io result is a 96% throughput collapse**.

**Full values:** [QPS](FULL_RESULTS.md#absolute-8-kib-qps)

| Payload | Role | Path | **Dart** | Node.js | Go |
|---:|---|---|---:|---:|---:|
| 1 KiB | server | io | **0.25×** | 0.83× | 0.88× |
| 16 KiB | server | io | **0.07×** | 0.62× | 0.57× |
| 64 KiB | server | io | **0.05×** | 0.34× | 0.29× |
| 1 MiB | server | io | **0.04×** | 0.33× | 0.08× |
| 1 KiB | server | http | **0.49×** | 0.74× | 0.84× |
| 16 KiB | server | http | **0.22×** | 0.67× | 0.77× |
| 64 KiB | server | http | **0.10×** | 0.68× | 0.59× |
| 1 MiB | server | http | **0.11×** | 0.41× | 0.36× |
| 1 KiB | client | io | **0.31×** | 0.66× | 1.30× |
| 16 KiB | client | io | **0.05×** | 0.59× | 0.77× |
| 64 KiB | client | io | **0.07×** | 0.72× | 0.30× |
| 1 MiB | client | io | **0.09×** | 0.61× | 0.15× |
| 1 KiB | client | http | **0.62×** | 0.71× | 0.87× |
| 16 KiB | client | http | **0.25×** | 0.81× | 0.83× |
| 64 KiB | client | http | **0.10×** | 0.54× | 0.69× |
| 1 MiB | client | http | **0.08×** | 0.52× | 0.48× |

### CPU ns/op

CPU/op reaches **22.94×** for 1 MiB server/io, compared with 3.07× for Node.js and 8.10× for Go. Dart remains at **9.30–22.94×** for every 1 MiB scenario.

**Full values:** [CPU ns/op](FULL_RESULTS.md#absolute-8-kib-target-cpu)

| Payload | Role | Path | **Dart** | Node.js | Go |
|---:|---|---|---:|---:|---:|
| 1 KiB | server | io | **6.48×** | 1.85× | 1.46× |
| 16 KiB | server | io | **21.29×** | 2.23× | 2.37× |
| 64 KiB | server | io | **19.05×** | 3.22× | 4.12× |
| 1 MiB | server | io | **22.94×** | 3.07× | 8.10× |
| 1 KiB | server | http | **2.06×** | 1.36× | 1.20× |
| 16 KiB | server | http | **4.53×** | 1.53× | 1.33× |
| 64 KiB | server | http | **10.49×** | 1.49× | 1.76× |
| 1 MiB | server | http | **9.30×** | 2.45× | 2.75× |
| 1 KiB | client | io | **3.23×** | 1.48× | 0.78× |
| 16 KiB | client | io | **20.52×** | 1.58× | 1.32× |
| 64 KiB | client | io | **14.70×** | 1.39× | 3.23× |
| 1 MiB | client | io | **10.63×** | 1.64× | 5.16× |
| 1 KiB | client | http | **1.62×** | 1.42× | 1.16× |
| 16 KiB | client | http | **3.93×** | 1.24× | 1.20× |
| 64 KiB | client | http | **10.50×** | 1.83× | 1.44× |
| 1 MiB | client | http | **12.88×** | 1.93× | 2.10× |

### System CPU ns/op

System CPU reaches **19.41×** for 16 KiB server/io, compared with 1.45× for Node.js and 1.81× for Go. This disproportionate system-time increase is consistent with excessive buffer movement across the TLS path.

**Full values:** [System CPU ns/op](FULL_RESULTS.md#absolute-8-kib-target-cpu)

| Payload | Role | Path | **Dart** | Node.js | Go |
|---:|---|---|---:|---:|---:|
| 1 KiB | server | io | **6.04×** | 1.52× | 1.36× |
| 16 KiB | server | io | **19.41×** | 1.45× | 1.81× |
| 64 KiB | server | io | **18.42×** | 1.71× | 3.10× |
| 1 MiB | server | io | **18.33×** | 1.51× | 4.21× |
| 1 KiB | server | http | **1.83×** | 1.18× | 1.12× |
| 16 KiB | server | http | **4.20×** | 1.19× | 1.17× |
| 64 KiB | server | http | **8.85×** | 0.89× | 1.50× |
| 1 MiB | server | http | **6.80×** | 1.15× | 1.99× |
| 1 KiB | client | io | **2.62×** | 1.08× | 0.70× |
| 16 KiB | client | io | **17.08×** | 0.76× | 0.82× |
| 64 KiB | client | io | **11.62×** | 0.49× | 1.87× |
| 1 MiB | client | io | **7.04×** | 0.48× | 2.54× |
| 1 KiB | client | http | **1.50×** | 1.18× | 1.11× |
| 16 KiB | client | http | **3.93×** | 0.81× | 1.11× |
| 64 KiB | client | http | **10.52×** | 1.05× | 1.21× |
| 1 MiB | client | http | **10.66×** | 1.00× | 1.57× |

### Latency p50

At 1 MiB, Dart TLS increases median latency by **13.29–21.50×**; Node.js is 1.93–4.58× and Go is 2.01–9.35×. The worst Dart result is **21.50× for server/io**.

**Full values:** [Latency p50](FULL_RESULTS.md#absolute-8-kib-latency)

| Payload | Role | Path | **Dart** | Node.js | Go |
|---:|---|---|---:|---:|---:|
| 1 KiB | server | io | **1.88×** | 1.24× | 1.13× |
| 16 KiB | server | io | **3.66×** | 1.35× | 1.31× |
| 64 KiB | server | io | **9.56×** | 2.02× | 1.32× |
| 1 MiB | server | io | **21.50×** | 3.17× | 9.35× |
| 1 KiB | server | http | **1.58×** | 1.04× | 1.03× |
| 16 KiB | server | http | **2.59×** | 1.19× | 1.08× |
| 64 KiB | server | http | **6.18×** | 1.28× | 1.19× |
| 1 MiB | server | http | **13.29×** | 2.20× | 2.01× |
| 1 KiB | client | io | **2.11×** | 1.03× | 1.04× |
| 16 KiB | client | io | **4.40×** | 1.45× | 1.21× |
| 64 KiB | client | io | **9.03×** | 1.80× | 1.80× |
| 1 MiB | client | io | **20.88×** | 4.58× | 5.36× |
| 1 KiB | client | http | **1.60×** | 1.12× | 1.05× |
| 16 KiB | client | http | **2.97×** | 1.19× | 1.01× |
| 64 KiB | client | http | **8.02×** | 1.35× | 1.19× |
| 1 MiB | client | http | **16.41×** | 1.93× | 2.31× |

### Cgroup peak

The **0.05× peak-memory coefficient** for 1 MiB server/io coincides with a **0.04× QPS coefficient**. Cgroup peak is process-level rather than memory/op, so this throughput-starved result is not evidence that Dart TLS uses less memory per operation. It is instead evidence of the bottleneck.

**Full values:** [Cgroup peak](FULL_RESULTS.md#absolute-8-kib-cgroup-memory)

| Payload | Role | Path | **Dart** | Node.js | Go |
|---:|---|---|---:|---:|---:|
| 1 KiB | server | io | **1.40×** | 1.02× | 1.26× |
| 16 KiB | server | io | **0.88×** | 0.91× | 1.26× |
| 64 KiB | server | io | **0.23×** | 0.62× | 1.32× |
| 1 MiB | server | io | **0.05×** | 0.58× | 1.43× |
| 1 KiB | server | http | **1.31×** | 1.36× | 1.13× |
| 16 KiB | server | http | **1.46×** | 1.65× | 1.09× |
| 64 KiB | server | http | **1.86×** | 1.39× | 1.06× |
| 1 MiB | server | http | **0.14×** | 1.17× | 1.16× |
| 1 KiB | client | io | **0.71×** | 0.94× | 1.44× |
| 16 KiB | client | io | **0.44×** | 0.81× | 0.88× |
| 64 KiB | client | io | **0.07×** | 0.97× | 0.39× |
| 1 MiB | client | io | **0.07×** | 1.19× | 0.91× |
| 1 KiB | client | http | **1.09×** | 1.08× | 0.90× |
| 16 KiB | client | http | **1.11×** | 1.17× | 0.92× |
| 64 KiB | client | http | **1.52×** | 0.79× | 1.06× |
| 1 MiB | client | http | **0.13×** | 1.11× | 1.48× |

## Improvements from configurable `SecurityContext.secureSocketBufferSize` (1 MiB payload)

The new buffer-size setting removes the fixed 8 KiB bottleneck. Selecting the highest-QPS tested setting per scenario raises throughput by **3.58–5.82×** while reducing CPU/op by **72–83%** and median latency by **73–81%**.

### Highest-QPS setting vs 8 KiB: throughput and CPU

The highest observed median-QPS setting is 128 KiB for `io` and 1 MiB for HTTP. At those settings, system CPU/op falls to **0.11–0.27×** even as QPS rises to **3.58–5.82×**.

**Full values:** [QPS](FULL_RESULTS.md#absolute-dart-buffer-sweep-qps) · [target CPU](FULL_RESULTS.md#absolute-dart-buffer-sweep-target-cpu)

| Role | Path | Buffer | QPS / 8 KiB | CPU/op / 8 KiB | System CPU/op / 8 KiB |
|---|---|---:|---:|---:|---:|
| server | io | 128 KiB | 4.21× | 0.24× | 0.23× |
| server | http | 1 MiB | 5.82× | 0.17× | 0.11× |
| client | io | 128 KiB | 3.58× | 0.28× | 0.27× |
| client | http | 1 MiB | 5.32× | 0.19× | 0.13× |

### Highest-QPS setting vs 8 KiB: latency and memory

p50 falls to **0.19–0.27×** and p99 falls to **0.22–0.28×**. The improvement trades for 1.00–1.15× current memory and 1.20–3.60× peak memory, depending on the scenario.

**Full values:** [latency](FULL_RESULTS.md#absolute-dart-buffer-sweep-latency) · [cgroup memory](FULL_RESULTS.md#absolute-dart-buffer-sweep-cgroup-memory)

| Role | Path | Buffer | p50 / 8 KiB | p99 / 8 KiB | Cgroup current / 8 KiB | Cgroup peak / 8 KiB |
|---|---|---:|---:|---:|---:|---:|
| server | io | 128 KiB | 0.27× | 0.28× | 1.14× | 1.20× |
| server | http | 1 MiB | 0.20× | 0.23× | 1.10× | 3.22× |
| client | io | 128 KiB | 0.22× | 0.25× | 1.15× | 1.23× |
| client | http | 1 MiB | 0.19× | 0.22× | 1.00× | 3.60× |

### Full sweep: QPS

Throughput peaks at 128 KiB for `io` and 1 MiB for HTTP. The strongest result is **5.82× QPS for server/http**.

**Full values:** [QPS and variability](FULL_RESULTS.md#absolute-dart-buffer-sweep-qps)

| Role | Path | Buffer | QPS | QPS / 8 KiB |
|---|---|---:|---:|---:|
| server | io | 8 KiB | 41 | 1.00× |
| server | io | 32 KiB | 107 | 2.59× |
| server | io | 128 KiB | 174 | 4.21× |
| server | io | 512 KiB | 152 | 3.68× |
| server | io | 1 MiB | 140 | 3.40× |
| server | http | 8 KiB | 63 | 1.00× |
| server | http | 32 KiB | 184 | 2.94× |
| server | http | 128 KiB | 327 | 5.22× |
| server | http | 512 KiB | 348 | 5.56× |
| server | http | 1 MiB | 365 | 5.82× |
| client | io | 8 KiB | 95 | 1.00× |
| client | io | 32 KiB | 282 | 2.96× |
| client | io | 128 KiB | 342 | 3.58× |
| client | io | 512 KiB | 302 | 3.17× |
| client | io | 1 MiB | 294 | 3.09× |
| client | http | 8 KiB | 50 | 1.00× |
| client | http | 32 KiB | 145 | 2.89× |
| client | http | 128 KiB | 261 | 5.21× |
| client | http | 512 KiB | 265 | 5.29× |
| client | http | 1 MiB | 267 | 5.32× |

### Full sweep: CPU

At the highest-QPS settings, CPU/op falls to **17–28% of the 8 KiB baseline** while target CPU remains near 97–97%, indicating that the same core completes substantially more work.

**Full values:** [target CPU](FULL_RESULTS.md#absolute-dart-buffer-sweep-target-cpu)

| Role | Path | Buffer | CPU ns/op | CPU / 8 KiB | Target CPU |
|---|---|---:|---:|---:|---:|
| server | io | 8 KiB | 24,020,563 | 1.00× | 96.9% |
| server | io | 32 KiB | 9,336,487 | 0.39× | 97.1% |
| server | io | 128 KiB | 5,745,928 | 0.24× | 96.7% |
| server | io | 512 KiB | 6,575,822 | 0.27× | 96.9% |
| server | io | 1 MiB | 7,128,982 | 0.30× | 96.5% |
| server | http | 8 KiB | 15,816,068 | 1.00× | 96.7% |
| server | http | 32 KiB | 5,413,232 | 0.34× | 96.7% |
| server | http | 128 KiB | 3,052,979 | 0.19× | 97.1% |
| server | http | 512 KiB | 2,868,986 | 0.18× | 97.5% |
| server | http | 1 MiB | 2,740,290 | 0.17× | 96.7% |
| client | io | 8 KiB | 10,474,372 | 1.00× | 96.9% |
| client | io | 32 KiB | 3,547,319 | 0.34× | 97.2% |
| client | io | 128 KiB | 2,925,465 | 0.28× | 97.1% |
| client | io | 512 KiB | 3,302,077 | 0.32× | 97.2% |
| client | io | 1 MiB | 3,392,119 | 0.32× | 96.9% |
| client | http | 8 KiB | 19,740,511 | 1.00× | 97.0% |
| client | http | 32 KiB | 6,869,370 | 0.35× | 96.9% |
| client | http | 128 KiB | 3,820,649 | 0.19× | 97.5% |
| client | http | 512 KiB | 3,766,669 | 0.19× | 97.2% |
| client | http | 1 MiB | 3,741,604 | 0.19× | 97.3% |

### Full sweep: CPU components

The highest-QPS settings reduce user CPU/op to 26–30% and system CPU/op to **11–27%** of the 8 KiB baseline. The largest system-time improvement is server/http: 8,904,754 to **945,476 ns/op**.

**Full values:** [target CPU](FULL_RESULTS.md#absolute-dart-buffer-sweep-target-cpu)

| Role | Path | Buffer | User ns/op | User / 8 KiB | System ns/op | System / 8 KiB |
|---|---|---:|---:|---:|---:|---:|
| server | io | 8 KiB | 9,086,326 | 1.00× | 15,140,406 | 1.00× |
| server | io | 32 KiB | 3,656,307 | 0.40× | 5,680,179 | 0.38× |
| server | io | 128 KiB | 2,324,304 | 0.26× | 3,417,389 | 0.23× |
| server | io | 512 KiB | 2,567,321 | 0.28× | 4,056,593 | 0.27× |
| server | io | 1 MiB | 2,757,403 | 0.30× | 4,397,886 | 0.29× |
| server | http | 8 KiB | 6,950,219 | 1.00× | 8,904,754 | 1.00× |
| server | http | 32 KiB | 2,542,801 | 0.37× | 2,870,431 | 0.32× |
| server | http | 128 KiB | 1,574,237 | 0.23× | 1,477,832 | 0.17× |
| server | http | 512 KiB | 1,772,347 | 0.26× | 1,108,765 | 0.12× |
| server | http | 1 MiB | 1,801,906 | 0.26× | 945,476 | 0.11× |
| client | io | 8 KiB | 4,859,467 | 1.00× | 5,617,050 | 1.00× |
| client | io | 32 KiB | 1,786,840 | 0.37× | 1,764,740 | 0.31× |
| client | io | 128 KiB | 1,464,754 | 0.30× | 1,489,098 | 0.27× |
| client | io | 512 KiB | 1,514,249 | 0.31× | 1,809,438 | 0.32× |
| client | io | 1 MiB | 1,555,371 | 0.32× | 1,836,747 | 0.33× |
| client | http | 8 KiB | 7,914,349 | 1.00× | 11,568,852 | 1.00× |
| client | http | 32 KiB | 3,080,497 | 0.39× | 3,788,857 | 0.33× |
| client | http | 128 KiB | 1,824,964 | 0.23× | 1,950,642 | 0.17× |
| client | http | 512 KiB | 2,095,695 | 0.26× | 1,611,490 | 0.14× |
| client | http | 1 MiB | 2,254,443 | 0.28× | 1,487,161 | 0.13× |

### Full sweep: latency mean and p50

The highest-QPS settings cut p50 from 16.64–25.64 ms to **3.62–6.71 ms**. The lowest p50 settings are 128 KiB for `io` and 512 KiB for HTTP.

**Full values:** [latency](FULL_RESULTS.md#absolute-dart-buffer-sweep-latency)

| Role | Path | Buffer | Mean | p50 | p50 / 8 KiB |
|---|---|---:|---:|---:|---:|
| server | io | 8 KiB | 24.68 ms | 24.40 ms | 1.00× |
| server | io | 32 KiB | 9.52 ms | 9.46 ms | 0.39× |
| server | io | 128 KiB | 6.74 ms | 6.71 ms | 0.27× |
| server | io | 512 KiB | 7.08 ms | 7.04 ms | 0.29× |
| server | io | 1 MiB | 7.36 ms | 7.35 ms | 0.30× |
| server | http | 8 KiB | 21.36 ms | 21.22 ms | 1.00× |
| server | http | 32 KiB | 6.78 ms | 6.74 ms | 0.32× |
| server | http | 128 KiB | 4.60 ms | 4.56 ms | 0.22× |
| server | http | 512 KiB | 4.09 ms | 4.06 ms | 0.19× |
| server | http | 1 MiB | 4.33 ms | 4.29 ms | 0.20× |
| client | io | 8 KiB | 16.69 ms | 16.64 ms | 1.00× |
| client | io | 32 KiB | 5.38 ms | 5.35 ms | 0.32× |
| client | io | 128 KiB | 3.66 ms | 3.62 ms | 0.22× |
| client | io | 512 KiB | 3.92 ms | 3.89 ms | 0.23× |
| client | io | 1 MiB | 3.98 ms | 3.95 ms | 0.24× |
| client | http | 8 KiB | 25.82 ms | 25.64 ms | 1.00× |
| client | http | 32 KiB | 8.05 ms | 8.01 ms | 0.31× |
| client | http | 128 KiB | 5.07 ms | 5.07 ms | 0.20× |
| client | http | 512 KiB | 4.56 ms | 4.54 ms | 0.18× |
| client | http | 1 MiB | 4.92 ms | 4.86 ms | 0.19× |

### Full sweep: latency p95 and p99

At the highest-QPS settings, p99 falls from 17.61–27.86 ms to **4.44–7.53 ms**. Tail latency can therefore be compared directly with the throughput-optimal buffer choice.

**Full values:** [latency](FULL_RESULTS.md#absolute-dart-buffer-sweep-latency)

| Role | Path | Buffer | p95 | p99 |
|---|---|---:|---:|---:|
| server | io | 8 KiB | 26.17 ms | 26.87 ms |
| server | io | 32 KiB | 10.13 ms | 10.43 ms |
| server | io | 128 KiB | 7.26 ms | 7.53 ms |
| server | io | 512 KiB | 7.81 ms | 8.17 ms |
| server | io | 1 MiB | 8.06 ms | 8.40 ms |
| server | http | 8 KiB | 22.78 ms | 23.36 ms |
| server | http | 32 KiB | 7.29 ms | 7.59 ms |
| server | http | 128 KiB | 5.07 ms | 5.31 ms |
| server | http | 512 KiB | 4.56 ms | 4.87 ms |
| server | http | 1 MiB | 4.80 ms | 5.28 ms |
| client | io | 8 KiB | 17.16 ms | 17.61 ms |
| client | io | 32 KiB | 5.67 ms | 5.95 ms |
| client | io | 128 KiB | 4.25 ms | 4.44 ms |
| client | io | 512 KiB | 4.44 ms | 4.66 ms |
| client | io | 1 MiB | 4.59 ms | 5.12 ms |
| client | http | 8 KiB | 27.40 ms | 27.86 ms |
| client | http | 32 KiB | 8.60 ms | 8.88 ms |
| client | http | 128 KiB | 5.67 ms | 6.01 ms |
| client | http | 512 KiB | 5.20 ms | 5.51 ms |
| client | http | 1 MiB | 5.74 ms | 6.18 ms |

### Full sweep: cgroup memory

Memory is the explicit trade-off: the highest-QPS settings use 1.20–3.60× peak memory. A 1 MiB buffer raises HTTP peak memory to **3.22–3.60×** of the 8 KiB baseline.

**Full values:** [cgroup memory](FULL_RESULTS.md#absolute-dart-buffer-sweep-cgroup-memory)

| Role | Path | Buffer | Current | Current / 8 KiB | Peak | Peak / 8 KiB |
|---|---|---:|---:|---:|---:|---:|
| server | io | 8 KiB | 9.0 MiB | 1.00× | 9.5 MiB | 1.00× |
| server | io | 32 KiB | 9.8 MiB | 1.09× | 10.4 MiB | 1.10× |
| server | io | 128 KiB | 10.2 MiB | 1.14× | 11.4 MiB | 1.20× |
| server | io | 512 KiB | 15.9 MiB | 1.77× | 17.2 MiB | 1.82× |
| server | io | 1 MiB | 19.1 MiB | 2.14× | 22.9 MiB | 2.41× |
| server | http | 8 KiB | 22.3 MiB | 1.00× | 23.8 MiB | 1.00× |
| server | http | 32 KiB | 31.9 MiB | 1.43× | 33.8 MiB | 1.42× |
| server | http | 128 KiB | 25.7 MiB | 1.15× | 50.0 MiB | 2.10× |
| server | http | 512 KiB | 17.2 MiB | 0.77× | 50.3 MiB | 2.11× |
| server | http | 1 MiB | 24.4 MiB | 1.10× | 76.6 MiB | 3.22× |
| client | io | 8 KiB | 8.9 MiB | 1.00× | 13.8 MiB | 1.00× |
| client | io | 32 KiB | 9.8 MiB | 1.10× | 14.7 MiB | 1.07× |
| client | io | 128 KiB | 10.2 MiB | 1.15× | 16.9 MiB | 1.23× |
| client | io | 512 KiB | 11.2 MiB | 1.26× | 20.4 MiB | 1.48× |
| client | io | 1 MiB | 15.1 MiB | 1.70× | 27.5 MiB | 2.00× |
| client | http | 8 KiB | 20.3 MiB | 1.00× | 22.6 MiB | 1.00× |
| client | http | 32 KiB | 26.6 MiB | 1.31× | 28.9 MiB | 1.28× |
| client | http | 128 KiB | 25.2 MiB | 1.24× | 51.4 MiB | 2.28× |
| client | http | 512 KiB | 14.4 MiB | 0.71× | 52.3 MiB | 2.32× |
| client | http | 1 MiB | 20.2 MiB | 1.00× | 81.3 MiB | 3.60× |

**Artifacts:** [FULL_RESULTS.md](FULL_RESULTS.md) · `cell_results.csv` · `summary.csv` · `environment.json` · `cells/<cell-id>/`
