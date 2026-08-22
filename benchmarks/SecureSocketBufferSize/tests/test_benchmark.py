import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import benchmark  # noqa: E402


class MatrixTest(unittest.TestCase):
    def test_quick_matrix_contract(self) -> None:
        cells = benchmark.make_cells(2, list(benchmark.PAYLOAD_SIZES))
        self.assertEqual(448, len(cells))
        self.assertEqual({"dart", "node", "go"}, {cell["language"] for cell in cells})
        self.assertEqual({"server", "client"}, {cell["target_role"] for cell in cells})
        self.assertEqual({"io", "http"}, {cell["protocol"] for cell in cells})
        self.assertEqual(
            {1024, 16 * 1024, 64 * 1024, 1024 * 1024},
            {cell["payload_bytes"] for cell in cells},
        )
        self.assertEqual({"latency", "throughput"}, {cell["kind"] for cell in cells})
        self.assertEqual(len(cells), len({cell["cell_id"] for cell in cells}))

    def test_dart_sweep_uses_every_configurable_size(self) -> None:
        cells = benchmark.make_cells(1, list(benchmark.PAYLOAD_SIZES))
        for target_role in benchmark.TARGET_ROLES:
            for protocol in benchmark.PROTOCOLS:
                sizes = {
                    cell["buffer_size"]
                    for cell in cells
                    if cell["language"] == "dart"
                    and cell["target_role"] == target_role
                    and cell["protocol"] == protocol
                    and cell["tls"]
                    and cell["payload_bytes"] == 1024 * 1024
                }
                self.assertEqual(set(benchmark.BUFFER_SIZES), sizes)


class ReportTest(unittest.TestCase):
    def test_generated_report_and_full_results_have_linked_data(self) -> None:
        payload = 1024 * 1024
        summary = []

        def add_row(
            language: str,
            role: str,
            protocol: str,
            tls: bool,
            kind: str,
            buffer_size: int,
            qps: float,
            cpu: float,
            p50: float,
            p99: float,
        ) -> None:
            summary.append({
                "language": language,
                "target_role": role,
                "protocol": protocol,
                "tls": tls,
                "payload_bytes": payload,
                "kind": kind,
                "buffer_size": buffer_size,
                "qps_median": qps,
                "qps_min": qps,
                "qps_max": qps,
                "qps_cv": 0,
                "target_cpu_ns_per_operation_median": cpu,
                "target_user_cpu_ns_per_operation_median": cpu * 0.4,
                "target_system_cpu_ns_per_operation_median": cpu * 0.6,
                "target_cpu_fraction_median": 0.7,
                "target_rss_bytes_median": 10 * 1024 * 1024,
                "target_peak_memory_bytes_median": 12 * 1024 * 1024,
                "latency_mean_ns_median": p50,
                "latency_p50_ns_median": p50,
                "latency_p95_ns_median": p99 * 0.9,
                "latency_p99_ns_median": p99,
            })

        secure_qps = {"dart": 100, "node": 500, "go": 400}
        secure_cpu = {"dart": 1000, "node": 200, "go": 300}
        for role in benchmark.TARGET_ROLES:
            for protocol in benchmark.PROTOCOLS:
                for language in ("dart", "node", "go"):
                    for tls in (False, True):
                        for kind in ("throughput", "latency"):
                            add_row(
                                language,
                                role,
                                protocol,
                                tls,
                                kind,
                                8 * 1024,
                                secure_qps[language] if tls else 1000,
                                secure_cpu[language] if tls else 100,
                                10_000_000 if tls and language == "dart" else 1_000_000,
                                12_000_000 if tls and language == "dart" else 2_000_000,
                            )
                for buffer_size in benchmark.BUFFER_SIZES[1:]:
                    factor = (
                        {32 * 1024: 2, 128 * 1024: 4, 512 * 1024: 3.5,
                         1024 * 1024: 3}[buffer_size]
                        if protocol == "io"
                        else {32 * 1024: 2, 128 * 1024: 3, 512 * 1024: 5,
                              1024 * 1024: 4}[buffer_size]
                    )
                    for kind in ("throughput", "latency"):
                        add_row(
                            "dart", role, protocol, True, kind, buffer_size,
                            100 * factor, 1000 / factor,
                            10_000_000 / factor, 12_000_000 / factor,
                        )

        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            benchmark.write_csv(run_dir / "summary.csv", summary, list(summary[0]))
            results = [{
                "status": "ok",
                "partner_cpu_fraction": 0.1,
                "target_throttled_periods": 0,
                "partner_throttled_periods": 0,
            }]
            benchmark.write_csv(
                run_dir / "cell_results.csv", results, list(results[0])
            )
            (run_dir / "environment.json").write_text(json.dumps({
                "versions": {
                    "dart": "dart-test", "node": "node-test", "go": "go-test",
                    "sdk_git_head": "deadbeef",
                },
                "topology": {
                    "physical_core_count": 8, "logical_cpu_count": 16,
                    "llc_source": "test",
                },
            }), encoding="utf-8")
            (run_dir / "run_metadata.json").write_text(json.dumps({
                "run_id": "report-test", "suite": "quick", "repetitions": 1,
                "wall_seconds": 60, "warmup_ms": 500, "throughput_ms": 1000,
                "latency_ms": 1500,
            }), encoding="utf-8")

            benchmark.build_report(run_dir)
            report = (run_dir / "REPORT.md").read_text(encoding="utf-8")
            full_results = (run_dir / benchmark.FULL_RESULTS_FILE).read_text(
                encoding="utf-8"
            )

        self.assertEqual([
            "## Benchmark setup",
            "## How to read this report",
            "## Finding: counterintuitive Dart TLS metrics at 8 KiB",
            "## Improvements from configurable `SecurityContext.secureSocketBufferSize` "
            "(1 MiB payload)",
        ], [line for line in report.splitlines() if line.startswith("## ")])
        self.assertIn("**Fairness controls:** role symmetry", report)
        self.assertIn(
            "This self-comparison cancels runtime implementation differences and "
            "benchmark-harness unfairness from the coefficient itself.",
            report,
        )
        self.assertIn("Dart TLS retains only **0.10×** of plain QPS", report)
        self.assertIn("It is instead evidence of the bottleneck.", report)
        self.assertIn(
            "The highest observed median-QPS setting is 128 KiB for `io` and "
            "512 KiB for HTTP",
            report,
        )
        self.assertIn(
            "**Artifacts:** [FULL_RESULTS.md](FULL_RESULTS.md) · `cell_results.csv`",
            report,
        )
        self.assertNotIn("## Files", report)
        self.assertNotIn("## Dart TLS buffer-size sweep", report)

        report_lines = report.splitlines()
        table_headers = [
            index for index in range(len(report_lines) - 1)
            if report_lines[index].startswith("|")
            and report_lines[index + 1].startswith("|---")
        ]
        self.assertGreater(len(table_headers), 0)
        for index in table_headers:
            previous = next(
                line for line in reversed(report_lines[:index]) if line
            )
            self.assertTrue(
                previous.startswith("**Full values:**"),
                f"missing full-values link before {report_lines[index]}",
            )

        self.assertIn("# Full benchmark results", full_results)
        self.assertIn("Values are medians across valid repetitions", full_results)
        for anchor in benchmark.FULL_RESULTS_ANCHORS.values():
            self.assertIn(f'<a id="{anchor}"></a>', full_results)
        self.assertEqual(
            8,
            sum(
                1 for index in range(len(full_results.splitlines()) - 1)
                if full_results.splitlines()[index].startswith("|")
                and full_results.splitlines()[index + 1].startswith("|---")
            ),
        )
        self.assertIn(
            "| Dart | server | io | no | 1 MiB | 1,000 | 1,000 | 1,000 | 0.0% |",
            full_results,
        )
        self.assertIn(
            "| Dart | server | io | yes | 1 MiB | 1,000 | 400 | 600 | 70.0% |",
            full_results,
        )
        self.assertIn(
            "| Dart | server | io | yes | 1 MiB | 10.00 ms | 10.00 ms | "
            "10.80 ms | 12.00 ms |",
            full_results,
        )
        self.assertIn(
            "| server | io | 128 KiB | 400 | 400 | 400 | 0.0% |",
            full_results,
        )

if __name__ == "__main__":
    unittest.main()
