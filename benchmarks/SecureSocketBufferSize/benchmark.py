from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psutil

from container_runtime import ContainerRuntime, IMAGES, command
from topology import LABEL, Topology, discover


ROOT = Path(__file__).resolve().parent
SDK_ROOT = ROOT.parents[1]
RESULTS = ROOT / "results"
CERTS = ROOT / "certs"
PROTOCOLS = ("io", "http")
TARGET_ROLES = ("server", "client")
PAYLOAD_SIZES = (1024, 16 * 1024, 64 * 1024, 1024 * 1024)
BUFFER_SIZES = (8 * 1024, 32 * 1024, 128 * 1024, 512 * 1024, 1024 * 1024)
FULL_RESULTS_FILE = "FULL_RESULTS.md"
FULL_RESULTS_ANCHORS = {
    "overview": "full-benchmark-results",
    "runtime_qps": "absolute-8-kib-qps",
    "runtime_cpu": "absolute-8-kib-target-cpu",
    "runtime_latency": "absolute-8-kib-latency",
    "runtime_memory": "absolute-8-kib-cgroup-memory",
    "sweep_qps": "absolute-dart-buffer-sweep-qps",
    "sweep_cpu": "absolute-dart-buffer-sweep-target-cpu",
    "sweep_latency": "absolute-dart-buffer-sweep-latency",
    "sweep_memory": "absolute-dart-buffer-sweep-cgroup-memory",
}
CSV_FIELDS = (
    "cell_id", "status", "invalid_reasons", "language", "target_role",
    "server_language", "client_language", "protocol", "tls", "payload_bytes",
    "kind", "window", "buffer_size", "repetition", "completed", "measured_operations",
    "elapsed_seconds",
    "qps", "latency_mean_ns", "latency_p50_ns", "latency_p95_ns", "latency_p99_ns",
    "errors", "target_cpuset", "partner_cpuset", "observer_cpuset",
    "target_cpu_s", "target_user_cpu_s", "target_system_cpu_s", "target_cpu_fraction",
    "target_cpu_ns_per_operation", "target_user_cpu_ns_per_operation",
    "target_system_cpu_ns_per_operation", "target_rss_bytes", "target_peak_memory_bytes",
    "target_throttled_periods", "partner_cpu_s", "partner_user_cpu_s",
    "partner_system_cpu_s", "partner_cpu_fraction", "partner_cpu_ns_per_operation",
    "partner_user_cpu_ns_per_operation", "partner_system_cpu_ns_per_operation",
    "partner_rss_bytes", "partner_peak_memory_bytes", "partner_throttled_periods",
    "resource_elapsed_seconds", "error",
)


def prepare() -> None:
    CERTS.mkdir(parents=True, exist_ok=True)
    cert = CERTS / "server.pem"
    key = CERTS / "server.key"
    if not cert.exists() or not key.exists():
        _run_visible([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", key, "-out", cert, "-days", "30", "-sha256",
            "-subj", "/CN=localhost",
            "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,digitalSignature,keyEncipherment,keyCertSign",
        ])

    builds = (
        ("observer", [
            "docker", "build", "--file", "workers/observer/Dockerfile",
            "--tag", IMAGES["observer"], ".",
        ], ROOT),
        ("go", [
            "docker", "build", "--file", "workers/go/Dockerfile",
            "--tag", IMAGES["go"], ".",
        ], ROOT),
        ("node", [
            "docker", "build", "--file", "workers/node/Dockerfile",
            "--tag", IMAGES["node"], ".",
        ], ROOT),
        ("dart branch SDK", [
            "docker", "build", "--file",
            "benchmarks/SecureSocketBufferSize/workers/dart/Dockerfile",
            "--tag", IMAGES["dart"], ".",
        ], SDK_ROOT),
    )
    for name, parts, cwd in builds:
        print(f"building {name} image...", flush=True)
        completed = subprocess.run(
            [str(part) for part in parts], cwd=cwd, timeout=7200
        )
        if completed.returncode:
            raise RuntimeError(f"{name} image build failed")
    write_json(ROOT / "build" / "versions.json", collect_versions())


def collect_versions() -> dict[str, Any]:
    def runtime_file(language: str) -> str:
        return command([
            "docker", "run", "--rm", "--entrypoint", "cat", IMAGES[language],
            "/app/runtime-version.txt",
        ]).stdout.strip()

    images = {}
    for language, image in IMAGES.items():
        inspected = json.loads(command([
            "docker", "image", "inspect", image, "--format", "{{json .}}"
        ]).stdout)
        images[language] = {
            "tag": image,
            "id": inspected["Id"],
            "created": inspected["Created"],
        }
    return {
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dart": runtime_file("dart"),
        "node": command([
            "docker", "run", "--rm", "--entrypoint", "node", IMAGES["node"], "--version"
        ]).stdout.strip(),
        "go": runtime_file("go"),
        "docker": command(["docker", "version", "--format", "{{.Server.Version}}"]).stdout.strip(),
        "sdk_git_head": _output(["git", "rev-parse", "HEAD"], cwd=SDK_ROOT),
        "images": images,
    }


def make_cells(repetitions: int, payloads: list[int]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for repetition in range(1, repetitions + 1):
        for language in ("dart", "node", "go"):
            for target_role in TARGET_ROLES:
                for protocol in PROTOCOLS:
                    for payload in payloads:
                        for tls_enabled in (False, True):
                            for kind, window in (("latency", 1), ("throughput", 8)):
                                cells.append({
                                    "language": language,
                                    "target_role": target_role,
                                    "protocol": protocol,
                                    "payload_bytes": payload,
                                    "tls": tls_enabled,
                                    "kind": kind,
                                    "window": window,
                                    "buffer_size": 8 * 1024,
                                    "repetition": repetition,
                                })
        for target_role in TARGET_ROLES:
            for protocol in PROTOCOLS:
                for buffer_size in BUFFER_SIZES[1:]:
                    for kind, window in (("latency", 1), ("throughput", 8)):
                        cells.append({
                            "language": "dart",
                            "target_role": target_role,
                            "protocol": protocol,
                            "payload_bytes": max(payloads),
                            "tls": True,
                            "kind": kind,
                            "window": window,
                            "buffer_size": buffer_size,
                            "repetition": repetition,
                        })
    random.Random(0xDAB7).shuffle(cells)
    for index, cell in enumerate(cells, 1):
        cell["cell_id"] = (
            f"{index:04d}-{cell['language']}-{cell['target_role']}-{cell['protocol']}-"
            f"{cell['kind']}-p{cell['payload_bytes']}-"
            f"{'tls' if cell['tls'] else 'plain'}-b{cell['buffer_size']}-r{cell['repetition']}"
        )
    return cells


def execute_suite(args: argparse.Namespace, *, smoke: bool) -> Path:
    if not _images_exist():
        prepare()
    run_id = args.run_id or (
        ("smoke" if smoke else "quick") + "-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    run_dir = RESULTS / run_id
    if run_dir.exists():
        raise FileExistsError(f"run already exists: {run_dir}")
    (run_dir / "cells").mkdir(parents=True)
    payloads = [64 * 1024] if smoke else list(PAYLOAD_SIZES)
    repetitions = 1 if smoke else args.repetitions
    cells = make_cells(repetitions, payloads)
    if smoke:
        selected: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()
        for cell in cells:
            key = (
                cell["language"], cell["target_role"], cell["protocol"], cell["tls"],
                cell["kind"],
                cell["buffer_size"]
                if cell["language"] == "dart" and cell["tls"]
                else 0,
            )
            endpoint = cell["buffer_size"] in (8 * 1024, 1024 * 1024)
            if key not in seen and (cell["language"] != "dart" or not cell["tls"] or endpoint):
                selected.append(cell)
                seen.add(key)
        cells = selected

    topology = discover()
    placements = {
        repetition: topology.placement(repetition) for repetition in range(1, repetitions + 1)
    }
    config = {
        "run_id": run_id,
        "suite": "smoke" if smoke else "quick",
        "repetitions": repetitions,
        "payloads": payloads,
        "warmup_ms": 200 if smoke else args.warmup_ms,
        "throughput_ms": 500 if smoke else args.throughput_ms,
        "latency_ms": 500 if smoke else args.latency_ms,
        "cells": len(cells),
        "seed": "0xDAB7",
        "target_cpus": 1,
        "partner_go_cpus": 4,
        "memory_per_container": "4 GiB, swap disabled",
    }
    write_json(run_dir / "plan.json", {**config, "matrix": cells})
    write_json(run_dir / "environment.json", environment(config, topology, placements))
    rows: list[dict[str, Any]] = []
    started = time.monotonic()
    runtime = ContainerRuntime(run_id, placements[1].observer_cpus)
    try:
        for index, cell in enumerate(cells, 1):
            print(
                f"[{index}/{len(cells)}] {cell['language']} target-{cell['target_role']} "
                f"{cell['protocol']} {cell['kind']} p={cell['payload_bytes']} "
                f"tls={cell['tls']} buffer={cell['buffer_size']}",
                flush=True,
            )
            row = run_cell(
                runtime,
                run_dir,
                cell,
                placements[int(cell["repetition"])],
                warmup_ms=int(config["warmup_ms"]),
                duration_ms=(
                    int(config["throughput_ms"])
                    if cell["kind"] == "throughput"
                    else int(config["latency_ms"])
                ),
            )
            rows.append(row)
            write_csv(run_dir / "cell_results.csv", rows, CSV_FIELDS)
            print(f"  {row['status']} qps={float(row.get('qps') or 0):,.1f}", flush=True)
    finally:
        runtime.close()
    config["wall_seconds"] = time.monotonic() - started
    write_json(run_dir / "run_metadata.json", config)
    build_summary(run_dir, rows)
    build_report(run_dir)
    print(f"results: {run_dir}")
    return run_dir


def run_cell(
    runtime: ContainerRuntime,
    run_dir: Path,
    cell: dict[str, Any],
    placement: Any,
    *,
    warmup_ms: int,
    duration_ms: int,
) -> dict[str, Any]:
    cell_dir = run_dir / "cells" / str(cell["cell_id"])
    cell_dir.mkdir(parents=True, exist_ok=True)
    write_json(cell_dir / "planned.json", {**cell, "placement": placement.as_dict()})
    try:
        result = runtime.run_cell(
            cell=cell,
            cell_dir=cell_dir,
            placement=placement,
            warmup_ms=warmup_ms,
            duration_ms=duration_ms,
        )
        row = normalize_resource_metrics({**cell, **result, "error": ""})
    except Exception as error:
        row = {
            **cell,
            "status": "failed",
            "invalid_reasons": "",
            "error": repr(error),
        }
    write_json(cell_dir / "result.json", row)
    return row


def environment(
    config: dict[str, Any], topology: Topology, placements: dict[int, Any]
) -> dict[str, Any]:
    versions_path = ROOT / "build" / "versions.json"
    return {
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host_platform": platform.platform(),
        "python": sys.version,
        "host_cpu_name": platform.processor(),
        "host_memory_bytes": psutil.virtual_memory().total,
        "versions": json.loads(versions_path.read_text(encoding="utf-8")),
        "topology": topology.as_dict(),
        "placements": {str(key): value.as_dict() for key, value in placements.items()},
        "benchmark_git_status": _output(["git", "status", "--short"], cwd=SDK_ROOT),
        "config": config,
    }


def build_summary(
    run_dir: Path, source_rows: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    rows = source_rows or read_csv(run_dir / "cell_results.csv")
    rows = [normalize_resource_metrics(row) for row in rows]
    write_csv(run_dir / "cell_results.csv", rows, CSV_FIELDS)
    valid = [row for row in rows if row.get("status") == "ok"]
    keys = (
        "language", "target_role", "protocol", "tls", "payload_bytes", "kind",
        "window", "buffer_size",
    )
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in valid:
        grouped.setdefault(tuple(str(row[name]) for name in keys), []).append(row)
    measures = (
        "qps", "latency_mean_ns", "latency_p50_ns", "latency_p95_ns", "latency_p99_ns",
        "target_cpu_s", "target_user_cpu_s", "target_system_cpu_s", "target_cpu_fraction",
        "target_cpu_ns_per_operation", "target_user_cpu_ns_per_operation",
        "target_system_cpu_ns_per_operation", "target_rss_bytes", "target_peak_memory_bytes",
        "target_throttled_periods", "partner_cpu_s", "partner_user_cpu_s",
        "partner_system_cpu_s", "partner_cpu_fraction", "partner_cpu_ns_per_operation",
        "partner_user_cpu_ns_per_operation", "partner_system_cpu_ns_per_operation",
        "partner_rss_bytes", "partner_peak_memory_bytes", "partner_throttled_periods",
    )
    summary: list[dict[str, Any]] = []
    for key, items in sorted(grouped.items()):
        row: dict[str, Any] = dict(zip(keys, key))
        row["runs"] = len(items)
        for measure in measures:
            row[f"{measure}_median"] = median(items, measure)
        qps_values = [float(item["qps"]) for item in items]
        row["qps_min"] = min(qps_values)
        row["qps_max"] = max(qps_values)
        row["qps_cv"] = (
            statistics.pstdev(qps_values) / statistics.mean(qps_values)
            if len(qps_values) > 1 and statistics.mean(qps_values)
            else 0
        )
        summary.append(row)
    write_csv(run_dir / "summary.csv", summary, list(summary[0]) if summary else ["language"])
    return summary


def normalize_resource_metrics(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("status") != "ok":
        return row
    required = ("completed", "window", "resource_elapsed_seconds")
    if any(row.get(name) in (None, "") for name in required):
        return row
    measured_operations = int(float(row["completed"])) + int(float(row["window"]))
    resource_elapsed = float(row["resource_elapsed_seconds"])
    row["measured_operations"] = measured_operations
    for role, cores in (("target", 1), ("partner", 4)):
        cpu_seconds = float(row[f"{role}_cpu_s"])
        row[f"{role}_cpu_fraction"] = (
            cpu_seconds / (resource_elapsed * cores) if resource_elapsed else 0
        )
        row[f"{role}_cpu_ns_per_operation"] = (
            cpu_seconds * 1e9 / measured_operations if measured_operations else 0
        )
        row[f"{role}_user_cpu_ns_per_operation"] = (
            float(row[f"{role}_user_cpu_s"]) * 1e9 / measured_operations
            if measured_operations else 0
        )
        row[f"{role}_system_cpu_ns_per_operation"] = (
            float(row[f"{role}_system_cpu_s"]) * 1e9 / measured_operations
            if measured_operations else 0
        )
    return row


def build_report(run_dir: Path) -> None:
    summary = read_csv(run_dir / "summary.csv")
    results = read_csv(run_dir / "cell_results.csv")
    environment_data = json.loads((run_dir / "environment.json").read_text(encoding="utf-8"))
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    failed = [row for row in results if row.get("status") != "ok"]
    payloads = sorted({int(row["payload_bytes"]) for row in summary})
    largest = payloads[-1] if payloads else 0

    def select(
        language: str,
        target_role: str,
        protocol: str,
        tls_enabled: bool,
        kind: str,
        buffer_size: int = 8 * 1024,
        payload: int = largest,
    ) -> dict[str, Any] | None:
        for row in summary:
            if (
                row["language"] == language
                and row["target_role"] == target_role
                and row["protocol"] == protocol
                and as_bool(row["tls"]) == tls_enabled
                and row["kind"] == kind
                and int(row["buffer_size"]) == buffer_size
                and int(row["payload_bytes"]) == payload
            ):
                return row
        return None

    throughput_cv = [value(row, "qps_cv") for row in summary if row["kind"] == "throughput"]
    noisy_throughput = sorted(
        (
            row for row in summary
            if row["kind"] == "throughput" and value(row, "qps_cv") >= 0.10
        ),
        key=lambda row: value(row, "qps_cv"),
        reverse=True,
    )
    valid_results = [row for row in results if row.get("status") == "ok"]
    max_partner_cpu = max(
        (float(row["partner_cpu_fraction"]) for row in valid_results), default=0
    )
    target_throttled = sum(
        int(float(row.get("target_throttled_periods") or 0)) > 0 for row in valid_results
    )
    partner_throttled = sum(
        int(float(row.get("partner_throttled_periods") or 0)) > 0 for row in valid_results
    )
    max_target_throttled = max(
        (int(float(row.get("target_throttled_periods") or 0)) for row in valid_results),
        default=0,
    )
    lines = [
        "# Secure socket buffer size benchmark report",
        "",
        "## Benchmark setup",
        "",
        _full_results_links(("all benchmark data", "overview")),
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Run | `{metadata['run_id']}`; {metadata['suite']}; "
        f"{metadata['repetitions']} repetitions; {metadata['wall_seconds'] / 60:.1f} min |",
        f"| Timing | warmup {metadata['warmup_ms']} ms; throughput "
        f"{metadata['throughput_ms']} ms; latency {metadata['latency_ms']} ms |",
        "| Workload | persistent `io` echo and HTTP/1.1 keep-alive; "
        "throughput window 8; latency window 1 |",
        "| CPU placement | target 1 core; fixed Go partner 4 cores; observer 1 core |",
        "| Network | separate Linux containers; shared network namespace; loopback |",
        "| Memory | 4 GiB per container; swap disabled |",
        f"| Runtimes | Dart: `{environment_data['versions']['dart']}`; "
        f"Node.js: `{environment_data['versions']['node']}`; "
        f"Go: `{environment_data['versions']['go']}` |",
        f"| Source | SDK `{environment_data['versions']['sdk_git_head']}` |",
        f"| Docker CPUs | {environment_data['topology']['physical_core_count']} physical / "
        f"{environment_data['topology']['logical_cpu_count']} logical; "
        f"LLC `{environment_data['topology']['llc_source']}` |",
        f"| Validity | {len(valid_results)}/{len(results)} cells; max QPS CV "
        f"{(max(throughput_cv) if throughput_cv else 0) * 100:.1f}%; "
        f"CV ≥10% in {len(noisy_throughput)} groups |",
        f"| Cgroup limits | target throttled in {target_throttled} cells "
        f"(max {max_target_throttled} periods); partner max CPU "
        f"{max_partner_cpu * 100:.1f}% of 4 cores; partner throttled in "
        f"{partner_throttled} cells |",
    ]
    if failed:
        lines.extend([
            "",
            f"> **Validity warning:** {len(failed)} cell(s) failed the execution or "
            "partner-headroom contract. "
            "They are excluded from medians; inspect `cell_results.csv`.",
        ])
    if noisy_throughput:
        lines.extend([
            "",
            "<details>",
            "<summary>Throughput groups with QPS CV ≥10%</summary>",
            "",
            _full_results_links(("QPS and variability", "runtime_qps")),
            "",
            "| Target | Role | Path | TLS | Payload | QPS range | CV |",
            "|---|---|---|---:|---:|---:|---:|",
        ])
        for row in noisy_throughput:
            lines.append(
                f"| {row['language'].title()} | {row['target_role']} | {row['protocol']} | "
                f"{'yes' if as_bool(row['tls']) else 'no'} | "
                f"{format_bytes(int(row['payload_bytes']))} | "
                f"{value(row, 'qps_min'):,.0f}–{value(row, 'qps_max'):,.0f} | "
                f"{value(row, 'qps_cv') * 100:.1f}% |"
            )
        lines.extend(["", "</details>"])
    lines.extend(_how_to_read())
    lines.extend(_cross_runtime_metric_tables(select, payloads))
    lines.extend(_dart_at_a_glance(select, largest))
    lines.extend(_dart_buffer_sweep(select, largest))
    lines.extend([
        "",
        f"**Artifacts:** [{FULL_RESULTS_FILE}]({FULL_RESULTS_FILE}) · "
        "`cell_results.csv` · `summary.csv` · `environment.json` · `cells/<cell-id>/`",
        "",
    ])
    build_full_results(run_dir, summary, largest)
    (run_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def _how_to_read() -> list[str]:
    return [
        "",
        "## How to read this report",
        "",
        "**Fairness controls:** role symmetry · fixed Go partner · pinned physical "
        "cores · no SMT siblings · partner headroom · isolated observer · identical "
        "loopback · fixed container limits · warmup barrier · deterministic order · "
        "repeated medians.",
        "",
        "Absolute results can still reflect differences between runtimes' I/O and "
        "HTTP implementations, as well as asymmetries in the benchmark harness. The "
        "main report therefore emphasizes TLS/plaintext coefficients instead of "
        "cross-runtime absolute values.",
        "",
        "Each coefficient compares a runtime with itself while holding the language, "
        "role, path, payload, window, and 8 KiB buffer constant; only TLS versus "
        "plaintext changes. This self-comparison cancels runtime implementation "
        "differences and benchmark-harness unfairness from the coefficient itself. "
        f"See the [full absolute results]({FULL_RESULTS_FILE}) when absolute values "
        "are needed.",
    ]


def build_full_results(
    run_dir: Path, summary: list[dict[str, Any]], largest: int
) -> None:
    baseline_throughput = _absolute_result_rows(
        summary, "throughput", largest, sweep=False
    )
    baseline_latency = _absolute_result_rows(
        summary, "latency", largest, sweep=False
    )
    sweep_throughput = _absolute_result_rows(
        summary, "throughput", largest, sweep=True
    )
    sweep_latency = _absolute_result_rows(
        summary, "latency", largest, sweep=True
    )
    lines = [
        f'<a id="{FULL_RESULTS_ANCHORS["overview"]}"></a>',
        "# Full benchmark results",
        "",
        "[Back to the benchmark report](REPORT.md)",
        "",
        "Values are medians across valid repetitions unless labeled as a minimum, "
        "maximum, or coefficient of variation (CV). These tables expose the absolute "
        "values behind the normalized comparisons in the main report. Per-repetition "
        "measurements remain available in `cell_results.csv`.",
        "",
        "## 8 KiB TLS/plaintext absolute results",
    ]
    lines.extend(_absolute_qps_table(baseline_throughput, sweep=False))
    lines.extend(_absolute_cpu_table(baseline_throughput, sweep=False))
    lines.extend(_absolute_latency_table(baseline_latency, sweep=False))
    lines.extend(_absolute_memory_table(baseline_throughput, sweep=False))
    lines.extend([
        "",
        f"## Dart TLS buffer-size sweep absolute results ({format_bytes(largest)} "
        "payload)",
    ])
    lines.extend(_absolute_qps_table(sweep_throughput, sweep=True))
    lines.extend(_absolute_cpu_table(sweep_throughput, sweep=True))
    lines.extend(_absolute_latency_table(sweep_latency, sweep=True))
    lines.extend(_absolute_memory_table(sweep_throughput, sweep=True))
    lines.append("")
    (run_dir / FULL_RESULTS_FILE).write_text("\n".join(lines), encoding="utf-8")


def _absolute_result_rows(
    summary: list[dict[str, Any]], kind: str, largest: int, *, sweep: bool
) -> list[dict[str, Any]]:
    if sweep:
        rows = [
            row for row in summary
            if row["kind"] == kind
            and row["language"] == "dart"
            and as_bool(row["tls"])
            and int(row["payload_bytes"]) == largest
        ]
    else:
        rows = [
            row for row in summary
            if row["kind"] == kind and int(row["buffer_size"]) == 8 * 1024
        ]
    language_order = {"dart": 0, "node": 1, "go": 2}
    return sorted(
        rows,
        key=lambda row: (
            TARGET_ROLES.index(row["target_role"]),
            PROTOCOLS.index(row["protocol"]),
            int(row["buffer_size"]) if sweep else int(row["payload_bytes"]),
            language_order.get(row["language"], len(language_order)),
            as_bool(row["tls"]),
        ),
    )


def _absolute_qps_table(
    rows: list[dict[str, Any]], *, sweep: bool
) -> list[str]:
    anchor = "sweep_qps" if sweep else "runtime_qps"
    lines = [
        "",
        f'<a id="{FULL_RESULTS_ANCHORS[anchor]}"></a>',
        "### QPS and variability",
        "",
        (
            "| Role | Path | Buffer | QPS median | QPS min | QPS max | CV |"
            if sweep else
            "| Target | Role | Path | TLS | Payload | QPS median | QPS min | QPS max | CV |"
        ),
        (
            "|---|---|---:|---:|---:|---:|---:|"
            if sweep else
            "|---|---|---|---:|---:|---:|---:|---:|---:|"
        ),
    ]
    for row in rows:
        dimensions = _absolute_dimensions(row, sweep=sweep)
        lines.append(
            f"| {dimensions} | {number(row, 'qps_median')} | "
            f"{number(row, 'qps_min')} | {number(row, 'qps_max')} | "
            f"{percent_plain(value(row, 'qps_cv'))} |"
        )
    return lines


def _absolute_cpu_table(
    rows: list[dict[str, Any]], *, sweep: bool
) -> list[str]:
    anchor = "sweep_cpu" if sweep else "runtime_cpu"
    lines = [
        "",
        f'<a id="{FULL_RESULTS_ANCHORS[anchor]}"></a>',
        "### Target CPU",
        "",
        (
            "| Role | Path | Buffer | CPU ns/op | User ns/op | System ns/op | Target CPU |"
            if sweep else
            "| Target | Role | Path | TLS | Payload | CPU ns/op | User ns/op | System ns/op | Target CPU |"
        ),
        (
            "|---|---|---:|---:|---:|---:|---:|"
            if sweep else
            "|---|---|---|---:|---:|---:|---:|---:|---:|"
        ),
    ]
    for row in rows:
        dimensions = _absolute_dimensions(row, sweep=sweep)
        lines.append(
            f"| {dimensions} | "
            f"{number(row, 'target_cpu_ns_per_operation_median')} | "
            f"{number(row, 'target_user_cpu_ns_per_operation_median')} | "
            f"{number(row, 'target_system_cpu_ns_per_operation_median')} | "
            f"{percent_plain(value(row, 'target_cpu_fraction_median'))} |"
        )
    return lines


def _absolute_latency_table(
    rows: list[dict[str, Any]], *, sweep: bool
) -> list[str]:
    anchor = "sweep_latency" if sweep else "runtime_latency"
    lines = [
        "",
        f'<a id="{FULL_RESULTS_ANCHORS[anchor]}"></a>',
        "### Latency",
        "",
        (
            "| Role | Path | Buffer | Mean | p50 | p95 | p99 |"
            if sweep else
            "| Target | Role | Path | TLS | Payload | Mean | p50 | p95 | p99 |"
        ),
        (
            "|---|---|---:|---:|---:|---:|---:|"
            if sweep else
            "|---|---|---|---:|---:|---:|---:|---:|---:|"
        ),
    ]
    for row in rows:
        dimensions = _absolute_dimensions(row, sweep=sweep)
        lines.append(
            f"| {dimensions} | {latency(row, 'latency_mean_ns_median')} | "
            f"{latency(row, 'latency_p50_ns_median')} | "
            f"{latency(row, 'latency_p95_ns_median')} | "
            f"{latency(row, 'latency_p99_ns_median')} |"
        )
    return lines


def _absolute_memory_table(
    rows: list[dict[str, Any]], *, sweep: bool
) -> list[str]:
    anchor = "sweep_memory" if sweep else "runtime_memory"
    lines = [
        "",
        f'<a id="{FULL_RESULTS_ANCHORS[anchor]}"></a>',
        "### Cgroup memory",
        "",
        (
            "| Role | Path | Buffer | Current | Peak |"
            if sweep else
            "| Target | Role | Path | TLS | Payload | Current | Peak |"
        ),
        (
            "|---|---|---:|---:|---:|"
            if sweep else
            "|---|---|---|---:|---:|---:|---:|"
        ),
    ]
    for row in rows:
        dimensions = _absolute_dimensions(row, sweep=sweep)
        lines.append(
            f"| {dimensions} | {mib(row, 'target_rss_bytes_median')} | "
            f"{mib(row, 'target_peak_memory_bytes_median')} |"
        )
    return lines


def _absolute_dimensions(row: dict[str, Any], *, sweep: bool) -> str:
    if sweep:
        return (
            f"{row['target_role']} | {row['protocol']} | "
            f"{format_bytes(int(row['buffer_size']))}"
        )
    language = {"dart": "Dart", "node": "Node.js", "go": "Go"}.get(
        row["language"], row["language"].title()
    )
    return (
        f"{language} | {row['target_role']} | {row['protocol']} | "
        f"{'yes' if as_bool(row['tls']) else 'no'} | "
        f"{format_bytes(int(row['payload_bytes']))}"
    )


def _full_results_links(*links: tuple[str, str]) -> str:
    rendered = [
        f"[{label}]({FULL_RESULTS_FILE}#{FULL_RESULTS_ANCHORS[anchor]})"
        for label, anchor in links
    ]
    return "**Full values:** " + " · ".join(rendered)


def _dart_at_a_glance(select: Any, largest: int) -> list[str]:
    selected: list[dict[str, Any]] = []
    for role in TARGET_ROLES:
        for protocol in PROTOCOLS:
            candidates = [
                (size, select("dart", role, protocol, True, "throughput", size))
                for size in BUFFER_SIZES
            ]
            candidates = [(size, row) for size, row in candidates if row]
            base = select("dart", role, protocol, True, "throughput")
            if not candidates or not base:
                continue
            best_size, best = max(candidates, key=lambda item: value(item[1], "qps_median"))
            selected.append({
                "role": role,
                "protocol": protocol,
                "buffer_size": best_size,
                "best": best,
                "base": base,
                "best_latency": select(
                    "dart", role, protocol, True, "latency", best_size
                ),
                "base_latency": select("dart", role, protocol, True, "latency"),
            })

    qps_ratios = _selected_ratios(selected, "best", "base", "qps_median")
    cpu_ratios = _selected_ratios(
        selected, "best", "base", "target_cpu_ns_per_operation_median"
    )
    system_ratios = _selected_ratios(
        selected, "best", "base", "target_system_cpu_ns_per_operation_median"
    )
    p50_ratios = _selected_ratios(
        selected, "best_latency", "base_latency", "latency_p50_ns_median"
    )
    p99_ratios = _selected_ratios(
        selected, "best_latency", "base_latency", "latency_p99_ns_median"
    )
    current_ratios = _selected_ratios(
        selected, "best", "base", "target_rss_bytes_median"
    )
    peak_ratios = _selected_ratios(
        selected, "best", "base", "target_peak_memory_bytes_median"
    )

    lines = [
        "",
        f"## Improvements from configurable `SecurityContext.secureSocketBufferSize` "
        f"({format_bytes(largest)} payload)",
        "",
        "The new buffer-size setting removes the fixed 8 KiB bottleneck. Selecting "
        "the highest-QPS tested setting per scenario raises throughput by "
        f"**{_ratio_range(qps_ratios)}** while reducing CPU/op by "
        f"**{_reduction_range(cpu_ratios)}** and median latency by "
        f"**{_reduction_range(p50_ratios)}**.",
        "",
        "### Highest-QPS setting vs 8 KiB: throughput and CPU",
        "",
        f"The highest observed median-QPS setting is {_best_settings_text(selected)}. "
        "At those "
        f"settings, system CPU/op falls to **{_ratio_range(system_ratios)}** even as "
        f"QPS rises to **{_ratio_range(qps_ratios)}**.",
        "",
        _full_results_links(
            ("QPS", "sweep_qps"), ("target CPU", "sweep_cpu")
        ),
        "",
        "| Role | Path | Buffer | QPS / 8 KiB | CPU/op / 8 KiB | "
        "System CPU/op / 8 KiB |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in selected:
        best = item["best"]
        base = item["base"]
        lines.append(
            f"| {item['role']} | {item['protocol']} | "
            f"{format_bytes(item['buffer_size'])} | "
            f"{ratio(best, base, 'qps_median')} | "
            f"{ratio(best, base, 'target_cpu_ns_per_operation_median')} | "
            f"{ratio(best, base, 'target_system_cpu_ns_per_operation_median')} |"
        )
    lines.extend([
        "",
        "### Highest-QPS setting vs 8 KiB: latency and memory",
        "",
        f"{_ratio_level_clause('p50', p50_ratios)} and "
        f"{_ratio_level_clause('p99', p99_ratios)}. The improvement trades for "
        f"{_ratio_range(current_ratios)} current memory and "
        f"{_ratio_range(peak_ratios)} peak memory, depending on the scenario.",
        "",
        _full_results_links(
            ("latency", "sweep_latency"), ("cgroup memory", "sweep_memory")
        ),
        "",
        "| Role | Path | Buffer | p50 / 8 KiB | p99 / 8 KiB | "
        "Cgroup current / 8 KiB | Cgroup peak / 8 KiB |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for item in selected:
        best = item["best"]
        base = item["base"]
        best_latency = item["best_latency"]
        base_latency = item["base_latency"]
        if not base or not base_latency or not best_latency:
            continue
        lines.append(
            f"| {item['role']} | {item['protocol']} | "
            f"{format_bytes(item['buffer_size'])} | "
            f"{ratio(best_latency, base_latency, 'latency_p50_ns_median')} | "
            f"{ratio(best_latency, base_latency, 'latency_p99_ns_median')} | "
            f"{ratio(best, base, 'target_rss_bytes_median')} | "
            f"{ratio(best, base, 'target_peak_memory_bytes_median')} |"
        )
    return lines


def _cross_runtime_metric_tables(select: Any, payloads: list[int]) -> list[str]:
    largest = max(payloads)
    lines = [
        "",
        "## Finding: counterintuitive Dart TLS metrics at 8 KiB",
        "",
        "Each unidirectional Dart TLS transfer traverses three of six buffers: four "
        "Dart native shared buffers (plain and encrypted, two each) and two BoringSSL "
        "BIO buffers. The TLS/plain coefficients below make the resulting allocation "
        "and copy pressure visible against the Node.js and Go baselines; `1.00×` is "
        "the corresponding plain-socket result.",
    ]
    metrics = (
        ("QPS", "throughput", "qps_median", "runtime_qps"),
        (
            "CPU ns/op",
            "throughput",
            "target_cpu_ns_per_operation_median",
            "runtime_cpu",
        ),
        (
            "System CPU ns/op",
            "throughput",
            "target_system_cpu_ns_per_operation_median",
            "runtime_cpu",
        ),
        ("Latency p50", "latency", "latency_p50_ns_median", "runtime_latency"),
        (
            "Cgroup peak",
            "throughput",
            "target_peak_memory_bytes_median",
            "runtime_memory",
        ),
    )
    for label, kind, field, anchor in metrics:
        metric_rows: list[dict[str, Any]] = []
        for role in TARGET_ROLES:
            for protocol in PROTOCOLS:
                for payload in payloads:
                    coefficients: dict[str, float | None] = {}
                    for language in ("dart", "node", "go"):
                        plain = select(
                            language, role, protocol, False, kind, payload=payload
                        )
                        secure = select(
                            language, role, protocol, True, kind, payload=payload
                        )
                        coefficients[language] = (
                            coefficient(secure, plain, field)
                            if plain and secure
                            else None
                        )
                    metric_rows.append({
                        "payload": payload,
                        "role": role,
                        "protocol": protocol,
                        "coefficients": coefficients,
                    })
        lines.extend([
            "",
            f"### {label}",
            "",
            _cross_runtime_summary(label, metric_rows, select, largest),
            "",
            _full_results_links((label, anchor)),
            "",
            "| Payload | Role | Path | **Dart** | Node.js | Go |",
            "|---:|---|---|---:|---:|---:|",
        ])
        for metric_row in metric_rows:
            coefficients = metric_row["coefficients"]
            rendered = [
                _ratio_text(coefficients[language])
                for language in ("dart", "node", "go")
            ]
            rendered[0] = f"**{rendered[0]}**"
            lines.append(
                f"| {format_bytes(metric_row['payload'])} | {metric_row['role']} | "
                f"{metric_row['protocol']} | " + " | ".join(rendered) + " |"
            )
    return lines


def _cross_runtime_summary(
    label: str,
    metric_rows: list[dict[str, Any]],
    select: Any,
    largest: int,
) -> str:
    largest_rows = [row for row in metric_rows if row["payload"] == largest]
    largest_dart = [
        row["coefficients"]["dart"]
        for row in largest_rows
        if row["coefficients"]["dart"] is not None
    ]
    if not largest_dart:
        return "Insufficient valid Dart rows to summarize this metric."

    if label == "QPS":
        worst = min(
            largest_rows,
            key=lambda row: _sortable_coefficient(row["coefficients"]["dart"], False),
        )
        worst_dart = worst["coefficients"]["dart"]
        loss = (1 - worst_dart) * 100 if worst_dart is not None else 0
        node = [
            row["coefficients"]["node"]
            for row in largest_rows
            if row["coefficients"]["node"] is not None
        ]
        go = [
            row["coefficients"]["go"]
            for row in largest_rows
            if row["coefficients"]["go"] is not None
        ]
        return (
            f"At {format_bytes(largest)}, Dart TLS retains only "
            f"**{_ratio_range(largest_dart)}** of plain QPS, versus "
            f"{_ratio_range(node)} for Node.js and {_ratio_range(go)} for Go. The "
            f"**{_ratio_text(worst_dart)} {worst['role']}/{worst['protocol']} result "
            f"is a {loss:.0f}% throughput collapse**."
        )

    if label in ("CPU ns/op", "System CPU ns/op"):
        worst = max(
            metric_rows,
            key=lambda row: _sortable_coefficient(row["coefficients"]["dart"], True),
        )
        coefficients = worst["coefficients"]
        metric_name = "CPU/op" if label == "CPU ns/op" else "System CPU"
        comparison = (
            f"{_ratio_text(coefficients['node'])} for Node.js and "
            f"{_ratio_text(coefficients['go'])} for Go"
        )
        first = (
            f"{metric_name} reaches **{_ratio_text(coefficients['dart'])}** for "
            f"{format_bytes(worst['payload'])} {worst['role']}/{worst['protocol']}, "
            f"compared with {comparison}."
        )
        if label == "CPU ns/op":
            return (
                f"{first} Dart remains at **{_ratio_range(largest_dart)}** for every "
                f"{format_bytes(largest)} scenario."
            )
        return (
            f"{first} This disproportionate system-time increase is consistent with "
            "excessive buffer movement across the TLS path."
        )

    if label == "Latency p50":
        worst = max(
            largest_rows,
            key=lambda row: _sortable_coefficient(row["coefficients"]["dart"], True),
        )
        node = [
            row["coefficients"]["node"]
            for row in largest_rows
            if row["coefficients"]["node"] is not None
        ]
        go = [
            row["coefficients"]["go"]
            for row in largest_rows
            if row["coefficients"]["go"] is not None
        ]
        return (
            f"At {format_bytes(largest)}, Dart TLS increases median latency by "
            f"**{_ratio_range(largest_dart)}**; Node.js is {_ratio_range(node)} and Go "
            f"is {_ratio_range(go)}. The worst Dart result is "
            f"**{_ratio_text(worst['coefficients']['dart'])} for "
            f"{worst['role']}/{worst['protocol']}**."
        )

    worst = min(
        largest_rows,
        key=lambda row: _sortable_coefficient(row["coefficients"]["dart"], False),
    )
    plain = select(
        "dart", worst["role"], worst["protocol"], False, "throughput",
        payload=largest,
    )
    secure = select(
        "dart", worst["role"], worst["protocol"], True, "throughput",
        payload=largest,
    )
    qps_coefficient = coefficient(secure, plain, "qps_median") if plain and secure else None
    return (
        f"The **{_ratio_text(worst['coefficients']['dart'])} peak-memory coefficient** "
        f"for {format_bytes(largest)} {worst['role']}/{worst['protocol']} coincides "
        f"with a **{_ratio_text(qps_coefficient)} QPS coefficient**. Cgroup peak is "
        "process-level rather than memory/op, so this throughput-starved result is not "
        "evidence that Dart TLS uses less memory per operation. It is instead evidence "
        "of the bottleneck."
    )


def _dart_buffer_sweep(select: Any, largest: int) -> list[str]:
    rows: list[tuple[str, str, int, dict[str, Any], dict[str, Any]]] = []
    for role in TARGET_ROLES:
        for protocol in PROTOCOLS:
            for buffer_size in BUFFER_SIZES:
                throughput = select(
                    "dart", role, protocol, True, "throughput", buffer_size
                )
                latency_row = select(
                    "dart", role, protocol, True, "latency", buffer_size
                )
                if throughput and latency_row:
                    rows.append(
                        (role, protocol, buffer_size, throughput, latency_row)
                    )

    best_rows = [
        max(
            (row for row in rows if row[0] == role and row[1] == protocol),
            key=lambda row: value(row[3], "qps_median"),
        )
        for role in TARGET_ROLES
        for protocol in PROTOCOLS
        if any(row[0] == role and row[1] == protocol for row in rows)
    ]
    largest_buffer = max((row[2] for row in rows), default=8 * 1024)
    best_settings = [
        {"role": role, "protocol": protocol, "buffer_size": buffer_size}
        for role, protocol, buffer_size, _, _ in best_rows
    ]
    if not best_rows:
        return ["", "### Full sweep", "", "No valid Dart TLS sweep rows are available."]
    strongest = max(
        best_rows,
        key=lambda row: coefficient(
            row[3], select("dart", row[0], row[1], True, "throughput"), "qps_median"
        ) or 0,
    )
    strongest_base = select("dart", strongest[0], strongest[1], True, "throughput")
    strongest_ratio = coefficient(strongest[3], strongest_base, "qps_median")
    cpu_range = _percent_of_baseline_range(
        _best_sweep_ratios(best_rows, select, "target_cpu_ns_per_operation_median")
    )
    user_cpu_range = _percent_of_baseline_range(
        _best_sweep_ratios(best_rows, select, "target_user_cpu_ns_per_operation_median")
    )
    system_cpu_range = _percent_of_baseline_range(
        _best_sweep_ratios(best_rows, select, "target_system_cpu_ns_per_operation_median")
    )
    target_cpu_range = _fraction_range([
        value(row[3], "target_cpu_fraction_median") for row in best_rows
    ])
    base_p50 = []
    for row in best_rows:
        base_latency = select("dart", row[0], row[1], True, "latency")
        if base_latency:
            base_p50.append(value(base_latency, "latency_p50_ns_median"))
    best_p50 = [value(row[4], "latency_p50_ns_median") for row in best_rows]
    peak_memory_range = _ratio_range(
        _best_sweep_ratios(best_rows, select, "target_peak_memory_bytes_median")
    )
    qps_summary = f"Throughput peaks at {_best_settings_text(best_settings)}"
    if all(row[2] != largest_buffer for row in best_rows):
        qps_summary += (
            f"; increasing the buffer to {format_bytes(largest_buffer)} does not "
            "improve any "
            "scenario further"
        )
    qps_summary += (
        f". The strongest result is **{_ratio_text(strongest_ratio)} "
        f"QPS for {strongest[0]}/{strongest[1]}**."
    )

    lines = [
        "",
        "### Full sweep: QPS",
        "",
        qps_summary,
        "",
        _full_results_links(("QPS and variability", "sweep_qps")),
        "",
        "| Role | Path | Buffer | QPS | QPS / 8 KiB |",
        "|---|---|---:|---:|---:|",
    ]
    for role, protocol, buffer_size, throughput, _ in rows:
        base = select("dart", role, protocol, True, "throughput")
        if base:
            lines.append(
                f"| {role} | {protocol} | {format_bytes(buffer_size)} | "
                f"{number(throughput, 'qps_median')} | "
                f"{ratio(throughput, base, 'qps_median')} |"
            )

    lines.extend([
        "",
        "### Full sweep: CPU",
        "",
        "At the highest-QPS settings, CPU/op falls to "
        f"**{cpu_range} "
        "of the 8 KiB baseline** while target CPU remains near "
        f"{target_cpu_range}, "
        "indicating that the same core completes substantially more work.",
        "",
        _full_results_links(("target CPU", "sweep_cpu")),
        "",
        "| Role | Path | Buffer | CPU ns/op | CPU / 8 KiB | Target CPU |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for role, protocol, buffer_size, throughput, _ in rows:
        base = select("dart", role, protocol, True, "throughput")
        if base:
            lines.append(
                f"| {role} | {protocol} | {format_bytes(buffer_size)} | "
                f"{number(throughput, 'target_cpu_ns_per_operation_median')} | "
                f"{ratio(throughput, base, 'target_cpu_ns_per_operation_median')} | "
                f"{percent_plain(value(throughput, 'target_cpu_fraction_median'))} |"
            )

    lines.extend([
        "",
        "### Full sweep: CPU components",
        "",
        "The highest-QPS settings reduce user CPU/op to "
        f"{user_cpu_range} "
        "and system CPU/op to "
        f"**{system_cpu_range}** "
        "of the 8 KiB baseline. "
        f"{_largest_system_cpu_improvement(best_rows, select)}",
        "",
        _full_results_links(("target CPU", "sweep_cpu")),
        "",
        "| Role | Path | Buffer | User ns/op | User / 8 KiB | System ns/op | "
        "System / 8 KiB |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for role, protocol, buffer_size, throughput, _ in rows:
        base = select("dart", role, protocol, True, "throughput")
        if base:
            lines.append(
                f"| {role} | {protocol} | {format_bytes(buffer_size)} | "
                f"{number(throughput, 'target_user_cpu_ns_per_operation_median')} | "
                f"{ratio(throughput, base, 'target_user_cpu_ns_per_operation_median')} | "
                f"{number(throughput, 'target_system_cpu_ns_per_operation_median')} | "
                f"{ratio(throughput, base, 'target_system_cpu_ns_per_operation_median')} |"
            )

    lines.extend([
        "",
        "### Full sweep: latency mean and p50",
        "",
        "The highest-QPS settings cut p50 from "
        f"{_latency_range(base_p50)} to **{_latency_range(best_p50)}**. "
        f"The lowest p50 settings are {_lowest_latency_settings_text(rows)}.",
        "",
        _full_results_links(("latency", "sweep_latency")),
        "",
        "| Role | Path | Buffer | Mean | p50 | p50 / 8 KiB |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for role, protocol, buffer_size, _, latency_row in rows:
        base = select("dart", role, protocol, True, "latency")
        if base:
            lines.append(
                f"| {role} | {protocol} | {format_bytes(buffer_size)} | "
                f"{latency(latency_row, 'latency_mean_ns_median')} | "
                f"{latency(latency_row, 'latency_p50_ns_median')} | "
                f"{ratio(latency_row, base, 'latency_p50_ns_median')} |"
            )

    lines.extend([
        "",
        "### Full sweep: latency p95 and p99",
        "",
        f"{_p99_sweep_summary(best_rows, select)} "
        "Tail latency can therefore be compared directly with the throughput-optimal "
        "buffer choice.",
        "",
        _full_results_links(("latency", "sweep_latency")),
        "",
        "| Role | Path | Buffer | p95 | p99 |",
        "|---|---|---:|---:|---:|",
    ])
    for role, protocol, buffer_size, _, latency_row in rows:
        lines.append(
            f"| {role} | {protocol} | {format_bytes(buffer_size)} | "
            f"{latency(latency_row, 'latency_p95_ns_median')} | "
            f"{latency(latency_row, 'latency_p99_ns_median')} |"
        )

    lines.extend([
        "",
        "### Full sweep: cgroup memory",
        "",
        "Memory is the explicit trade-off: the highest-QPS settings use "
        f"{peak_memory_range} "
        "peak memory. "
        f"{_largest_http_memory_summary(rows, select, largest_buffer)}",
        "",
        _full_results_links(("cgroup memory", "sweep_memory")),
        "",
        "| Role | Path | Buffer | Current | Current / 8 KiB | Peak | "
        "Peak / 8 KiB |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for role, protocol, buffer_size, throughput, _ in rows:
        base = select("dart", role, protocol, True, "throughput")
        if base:
            lines.append(
                f"| {role} | {protocol} | {format_bytes(buffer_size)} | "
                f"{mib(throughput, 'target_rss_bytes_median')} | "
                f"{ratio(throughput, base, 'target_rss_bytes_median')} | "
                f"{mib(throughput, 'target_peak_memory_bytes_median')} | "
                f"{ratio(throughput, base, 'target_peak_memory_bytes_median')} |"
            )
    return lines


def retry_failed(run_dir: Path, max_attempts: int) -> None:
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    environment_data = json.loads((run_dir / "environment.json").read_text(encoding="utf-8"))
    topology = discover()
    placements = {
        repetition: topology.placement(repetition)
        for repetition in range(1, int(metadata["repetitions"]) + 1)
    }
    rows = read_csv(run_dir / "cell_results.csv")
    runtime = ContainerRuntime(str(metadata["run_id"]), placements[1].observer_cpus)
    try:
        for index, source in enumerate(rows):
            if source.get("status") == "ok":
                continue
            planned = json.loads(
                (run_dir / "cells" / source["cell_id"] / "planned.json").read_text(encoding="utf-8")
            )
            planned.pop("placement", None)
            for _ in range(max_attempts):
                replacement = run_cell(
                    runtime,
                    run_dir,
                    planned,
                    placements[int(planned["repetition"])],
                    warmup_ms=int(metadata["warmup_ms"]),
                    duration_ms=(
                        int(metadata["throughput_ms"])
                        if planned["kind"] == "throughput"
                        else int(metadata["latency_ms"])
                    ),
                )
                source = replacement
                if replacement["status"] == "ok":
                    break
            rows[index] = source
    finally:
        runtime.close()
    write_csv(run_dir / "cell_results.csv", rows, CSV_FIELDS)
    build_summary(run_dir, rows)
    build_report(run_dir)


def _images_exist() -> bool:
    return all(
        command(["docker", "image", "inspect", image], check=False).returncode == 0
        for image in IMAGES.values()
    ) and (ROOT / "build" / "versions.json").exists()


def write_json(path: Path, value_: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value_, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...] | list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def median(items: list[dict[str, Any]], field: str) -> float:
    values = [float(item[field]) for item in items if item.get(field) not in (None, "")]
    return statistics.median(values) if values else 0.0


def as_bool(value_: Any) -> bool:
    return str(value_).lower() == "true"


def value(row: dict[str, Any], field: str) -> float:
    return float(row[field])


def coefficient(
    numerator: dict[str, Any] | None,
    denominator: dict[str, Any] | None,
    field: str,
) -> float | None:
    if not numerator or not denominator:
        return None
    base = value(denominator, field)
    return value(numerator, field) / base if base else None


def _ratio_text(value_: float | None) -> str:
    return f"{value_:.2f}×" if value_ is not None else "n/a"


def _ratio_range(values: list[float]) -> str:
    if not values:
        return "n/a"
    low, high = min(values), max(values)
    return _ratio_text(low) if low == high else f"{low:.2f}–{high:.2f}×"


def _percentage_range(values: list[float]) -> str:
    if not values:
        return "n/a"
    low, high = min(values), max(values)
    return f"{low:.0f}%" if low == high else f"{low:.0f}–{high:.0f}%"


def _reduction_range(ratios: list[float]) -> str:
    return _percentage_range([(1 - value_) * 100 for value_ in ratios])


def _percent_of_baseline_range(ratios: list[float]) -> str:
    return _percentage_range([value_ * 100 for value_ in ratios])


def _fraction_range(values: list[float]) -> str:
    return _percentage_range([value_ * 100 for value_ in values])


def _ratio_level_clause(subject: str, ratios: list[float]) -> str:
    if ratios and max(ratios) <= 1:
        verb = "falls"
    elif ratios and min(ratios) >= 1:
        verb = "rises"
    else:
        verb = "changes"
    return f"{subject} {verb} to **{_ratio_range(ratios)}**"


def _selected_ratios(
    selected: list[dict[str, Any]],
    numerator_key: str,
    denominator_key: str,
    field: str,
) -> list[float]:
    values: list[float] = []
    for item in selected:
        numerator = item.get(numerator_key)
        denominator = item.get(denominator_key)
        if numerator and denominator:
            value_ = coefficient(numerator, denominator, field)
            if value_ is not None:
                values.append(value_)
    return values


def _best_settings_text(selected: list[dict[str, Any]]) -> str:
    by_protocol: dict[str, set[int]] = {}
    for item in selected:
        by_protocol.setdefault(item["protocol"], set()).add(int(item["buffer_size"]))
    if by_protocol and all(len(sizes) == 1 for sizes in by_protocol.values()):
        all_sizes = {next(iter(sizes)) for sizes in by_protocol.values()}
        if len(all_sizes) == 1 and set(by_protocol) == set(PROTOCOLS):
            return f"{format_bytes(next(iter(all_sizes)))} for both `io` and HTTP"
        parts = []
        for protocol in PROTOCOLS:
            if protocol not in by_protocol:
                continue
            label = "`io`" if protocol == "io" else protocol.upper()
            parts.append(f"{format_bytes(next(iter(by_protocol[protocol])))} for {label}")
        return _join_words(parts)
    return _join_words([
        f"{format_bytes(item['buffer_size'])} for {item['role']}/{item['protocol']}"
        for item in selected
    ])


def _join_words(parts: list[str]) -> str:
    if not parts:
        return "n/a"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _sortable_coefficient(value_: float | None, highest: bool) -> float:
    if value_ is not None:
        return value_
    return float("-inf") if highest else float("inf")


def _best_sweep_ratios(
    best_rows: list[tuple[str, str, int, dict[str, Any], dict[str, Any]]],
    select: Any,
    field: str,
) -> list[float]:
    values: list[float] = []
    for role, protocol, _, throughput, _ in best_rows:
        base = select("dart", role, protocol, True, "throughput")
        if base:
            value_ = coefficient(throughput, base, field)
            if value_ is not None:
                values.append(value_)
    return values


def _largest_system_cpu_improvement(
    best_rows: list[tuple[str, str, int, dict[str, Any], dict[str, Any]]],
    select: Any,
) -> str:
    candidates = []
    for row in best_rows:
        base = select("dart", row[0], row[1], True, "throughput")
        if base:
            value_ = coefficient(
                row[3], base, "target_system_cpu_ns_per_operation_median"
            )
            if value_ is not None:
                candidates.append((value_, row, base))
    if not candidates:
        return "No valid system CPU comparison is available."
    _, best, base = min(candidates, key=lambda item: item[0])
    return (
        f"The largest system-time improvement is {best[0]}/{best[1]}: "
        f"{number(base, 'target_system_cpu_ns_per_operation_median')} to "
        f"**{number(best[3], 'target_system_cpu_ns_per_operation_median')} ns/op**."
    )


def _lowest_latency_settings_text(
    rows: list[tuple[str, str, int, dict[str, Any], dict[str, Any]]],
) -> str:
    selected = []
    for role in TARGET_ROLES:
        for protocol in PROTOCOLS:
            candidates = [row for row in rows if row[0] == role and row[1] == protocol]
            if candidates:
                best = min(candidates, key=lambda row: value(row[4], "latency_p50_ns_median"))
                selected.append({
                    "role": role,
                    "protocol": protocol,
                    "buffer_size": best[2],
                })
    return _best_settings_text(selected)


def _largest_http_memory_summary(
    rows: list[tuple[str, str, int, dict[str, Any], dict[str, Any]]],
    select: Any,
    largest: int,
) -> str:
    ratios = []
    largest_is_best = False
    for role in TARGET_ROLES:
        candidates = [row for row in rows if row[0] == role and row[1] == "http"]
        largest_row = next((row for row in candidates if row[2] == largest), None)
        base = select("dart", role, "http", True, "throughput")
        if largest_row and base:
            value_ = coefficient(
                largest_row[3], base, "target_peak_memory_bytes_median"
            )
            if value_ is not None:
                ratios.append(value_)
            best = max(candidates, key=lambda row: value(row[3], "qps_median"))
            largest_is_best = largest_is_best or best[2] == largest
    summary = (
        f"A {format_bytes(largest)} buffer raises HTTP peak memory to "
        f"**{_ratio_range(ratios)}** of the 8 KiB baseline"
    )
    if not largest_is_best:
        summary += " without delivering the highest QPS"
    return summary + "."


def _p99_sweep_summary(
    best_rows: list[tuple[str, str, int, dict[str, Any], dict[str, Any]]],
    select: Any,
) -> str:
    bases = [
        select("dart", row[0], row[1], True, "latency")
        for row in best_rows
    ]
    base_values = [
        value(base, "latency_p99_ns_median") for base in bases if base
    ]
    best_values = [value(row[4], "latency_p99_ns_median") for row in best_rows]
    ratios = [
        coefficient(row[4], base, "latency_p99_ns_median")
        for row, base in zip(best_rows, bases)
        if base
    ]
    ratios = [value_ for value_ in ratios if value_ is not None]
    if ratios and max(ratios) <= 1:
        verb = "falls"
    elif ratios and min(ratios) >= 1:
        verb = "rises"
    else:
        verb = "changes"
    return (
        f"At the highest-QPS settings, p99 {verb} from "
        f"{_latency_range(base_values)} to **{_latency_range(best_values)}**."
    )


def _latency_range(values: list[float]) -> str:
    if not values:
        return "n/a"
    low, high = min(values), max(values)
    if low == high:
        return _latency_text(low)
    if low >= 1e6:
        return f"{low / 1e6:.2f}–{high / 1e6:.2f} ms"
    if high < 1e6:
        return f"{low / 1e3:.1f}–{high / 1e3:.1f} µs"
    return f"{_latency_text(low)}–{_latency_text(high)}"


def _latency_text(nanoseconds: float) -> str:
    return (
        f"{nanoseconds / 1e6:.2f} ms"
        if nanoseconds >= 1e6
        else f"{nanoseconds / 1e3:.1f} µs"
    )


def number(row: dict[str, Any], field: str) -> str:
    return f"{value(row, field):,.0f}"


def ratio(numerator: dict[str, Any], denominator: dict[str, Any], field: str) -> str:
    return _ratio_text(coefficient(numerator, denominator, field))


def percent_plain(value_: float) -> str:
    return f"{value_ * 100:.1f}%"


def mib(row: dict[str, Any], field: str) -> str:
    return f"{value(row, field) / (1024 * 1024):,.1f} MiB"


def latency(row: dict[str, Any], field: str) -> str:
    nanoseconds = value(row, field)
    return f"{nanoseconds / 1e6:.2f} ms" if nanoseconds >= 1e6 else f"{nanoseconds / 1e3:.1f} µs"


def format_bytes(bytes_: int) -> str:
    if bytes_ >= 1024 * 1024:
        return f"{bytes_ / (1024 * 1024):g} MiB"
    return f"{bytes_ / 1024:g} KiB"


def _run_visible(parts: list[str | Path]) -> None:
    rendered = subprocess.list2cmdline([str(part) for part in parts])
    print(f"+ {rendered}", flush=True)
    subprocess.run([str(part) for part in parts], check=True, cwd=ROOT)


def _output(parts: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(parts, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def latest_run() -> Path:
    runs = sorted(
        (path for path in RESULTS.glob("*") if (path / "cell_results.csv").exists()),
        key=lambda path: path.stat().st_mtime,
    )
    if not runs:
        raise FileNotFoundError("no completed runs")
    return runs[-1]


def cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare", help="build the isolated worker images")
    for name in ("smoke", "quick"):
        child = commands.add_parser(name, help=f"run the {name} suite")
        child.add_argument("--run-id")
        child.add_argument("--repetitions", type=int, default=2)
        child.add_argument("--warmup-ms", type=int, default=500)
        child.add_argument("--throughput-ms", type=int, default=2000)
        child.add_argument("--latency-ms", type=int, default=1500)
    for name in ("report", "retry"):
        child = commands.add_parser(name, help=f"{name} an existing run")
        child.add_argument("--run-id")
        if name == "retry":
            child.add_argument("--max-attempts", type=int, default=3)
    return parser


def main() -> None:
    args = cli().parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "smoke":
        execute_suite(args, smoke=True)
    elif args.command == "quick":
        execute_suite(args, smoke=False)
    elif args.command == "report":
        run_dir = RESULTS / args.run_id if args.run_id else latest_run()
        build_summary(run_dir)
        build_report(run_dir)
        print(run_dir / "REPORT.md")
    elif args.command == "retry":
        run_dir = RESULTS / args.run_id if args.run_id else latest_run()
        retry_failed(run_dir, args.max_attempts)
        print(run_dir / "REPORT.md")


if __name__ == "__main__":
    main()
