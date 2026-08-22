from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from topology import CpuPlacement, LABEL, cpuset


IMAGES = {
    "dart": "dart-secure-socket-buffer-benchmark:local",
    "node": "node-secure-socket-buffer-benchmark:local",
    "go": "go-secure-socket-buffer-benchmark:local",
    "observer": "secure-socket-buffer-observer:local",
}
MEMORY = "4g"
MEMORY_BYTES = 4 * 1024 * 1024 * 1024
PORT = 43210


def command(
    parts: list[str | Path],
    *,
    cwd: Path | None = None,
    check: bool = True,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [str(part) for part in parts],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if check and completed.returncode:
        rendered = subprocess.list2cmdline([str(part) for part in parts])
        raise RuntimeError(
            f"command failed ({completed.returncode}): {rendered}\n"
            f"{completed.stdout}{completed.stderr}"
        )
    return completed


class ContainerRuntime:
    def __init__(self, run_id: str, observer_cpus: tuple[int, ...]) -> None:
        self.run_id = _safe(run_id)
        self.observer_name = f"ssbs-observer-{self.run_id}"[:63]
        command(["docker", "rm", "-f", self.observer_name], check=False)
        self.observer_id = command([
            "docker", "run", "-d", "--name", self.observer_name,
            "--network", "none", "--cpuset-cpus", cpuset(observer_cpus),
            "--cpus", str(len(observer_cpus)),
            "--memory", "128m", "--memory-swap", "128m",
            "--label", f"{LABEL}=true",
            "--volume", "/sys/fs/cgroup:/host-cgroup:ro",
            IMAGES["observer"],
        ]).stdout.strip()

    def close(self) -> None:
        command(["docker", "rm", "-f", self.observer_id], check=False)

    def run_cell(
        self,
        *,
        cell: dict[str, Any],
        cell_dir: Path,
        placement: CpuPlacement,
        warmup_ms: int,
        duration_ms: int,
    ) -> dict[str, Any]:
        cell_dir.mkdir(parents=True, exist_ok=True)
        barrier = cell_dir / "measure.go"
        ack = Path(f"{barrier}.ack")
        for marker in (barrier, ack):
            marker.unlink(missing_ok=True)

        target_role = str(cell["target_role"])
        target_language = str(cell["language"])
        server_language = target_language if target_role == "server" else "go"
        client_language = "go" if target_role == "server" else target_language
        server_cpus = placement.target_cpus if target_role == "server" else placement.partner_cpus
        client_cpus = placement.partner_cpus if target_role == "server" else placement.target_cpus
        server_role = "target" if target_role == "server" else "partner"
        client_role = "partner" if target_role == "server" else "target"

        suffix = _safe(str(cell["cell_id"]))[-40:]
        server_name = f"ssbs-server-{self.run_id}-{suffix}"[:63]
        client_name = f"ssbs-client-{self.run_id}-{suffix}"[:63]
        server_id = ""
        client_id = ""
        try:
            common = [
                f"--protocol={cell['protocol']}", f"--port={PORT}",
                f"--payload={cell['payload_bytes']}",
                f"--tls={str(cell['tls']).lower()}",
                f"--buffer-size={cell['buffer_size']}",
                "--cert=/app/certs/server.pem", "--key=/app/certs/server.key",
                "--ca=/app/certs/server.pem", f"--warmup-ms={warmup_ms}",
                f"--duration-ms={duration_ms}", f"--window={cell['window']}",
                "--barrier=/cell/measure.go",
            ]
            server_id = self._start(
                name=server_name,
                language=server_language,
                cpus=server_cpus,
                network="none",
                volume=cell_dir,
                args=["--mode=server", *common],
            )
            self._wait_event(server_id, "ready", 30)
            client_id = self._start(
                name=client_name,
                language=client_language,
                cpus=client_cpus,
                network=f"container:{server_id}",
                volume=cell_dir,
                args=["--mode=client", *common],
            )
            self._wait_event(client_id, "measurement_ready", 40 + warmup_ms / 1000)

            ids = {server_role: server_id, client_role: client_id}
            before = {
                role: self._snapshot(container_id) for role, container_id in ids.items()
            }
            before["captured_monotonic"] = time.monotonic()
            contracts = {
                role: self._contract(
                    container_id,
                    placement.target_cpus if role == "target" else placement.partner_cpus,
                )
                for role, container_id in ids.items()
            }
            barrier.write_text("go\n", encoding="ascii")
            result = self._wait_event(client_id, "result", 45 + duration_ms / 1000)
            after = {
                role: self._snapshot(container_id) for role, container_id in ids.items()
            }
            after["captured_monotonic"] = time.monotonic()
            ack.write_text("ack\n", encoding="ascii")
            exit_code = int(command(["docker", "wait", client_id], timeout=15).stdout.strip())
            resources = _resource_summary(
                before,
                after,
                completed=int(result.get("completed") or 0),
                window=int(cell["window"]),
            )
            invalid: list[str] = []
            if exit_code:
                invalid.append(f"client exit code {exit_code}")
            if int(result.get("errors") or 0):
                invalid.append(f"operation errors: {result['errors']}")
            for role, contract in contracts.items():
                if contract["mismatches"]:
                    invalid.append(
                        f"{role} container contract mismatch: "
                        + "; ".join(str(item) for item in contract["mismatches"])
                    )
            if float(resources["partner_cpu_fraction"]) >= 0.90:
                invalid.append("four-core Go partner used at least 90% aggregate CPU")
            details = {
                "before": before,
                "after": after,
                "contracts": contracts,
                "server": {"id": server_id, "language": server_language, "role": server_role},
                "client": {"id": client_id, "language": client_language, "role": client_role},
                "summary": resources,
            }
            (cell_dir / "resources.json").write_text(
                json.dumps(details, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return {
                **{key: value for key, value in result.items() if key != "event"},
                **resources,
                "status": "ok" if not invalid else "invalid",
                "invalid_reasons": "; ".join(invalid),
                "target_cpuset": cpuset(placement.target_cpus),
                "partner_cpuset": cpuset(placement.partner_cpus),
                "observer_cpuset": cpuset(placement.observer_cpus),
                "server_language": server_language,
                "client_language": client_language,
            }
        finally:
            for container_id, log_name in (
                (client_id, "client.log"),
                (server_id, "server.log"),
            ):
                if not container_id:
                    continue
                logs = command(["docker", "logs", container_id], check=False)
                (cell_dir / log_name).write_text(
                    logs.stdout + logs.stderr, encoding="utf-8"
                )
                command(["docker", "rm", "-f", container_id], check=False)

    def _start(
        self,
        *,
        name: str,
        language: str,
        cpus: tuple[int, ...],
        network: str,
        volume: Path,
        args: list[str],
    ) -> str:
        command(["docker", "rm", "-f", name], check=False)
        return command([
            "docker", "run", "-d", "--name", name,
            "--network", network,
            "--cpuset-cpus", cpuset(cpus), "--cpus", str(len(cpus)),
            "--memory", MEMORY, "--memory-swap", MEMORY,
            "--pids-limit", "4096", "--label", f"{LABEL}=true",
            "--env", f"GOMAXPROCS={len(cpus)}",
            "--volume", f"{volume.resolve()}:/cell",
            IMAGES[language], *args,
        ]).stdout.strip()

    def _snapshot(self, container_id: str) -> dict[str, Any]:
        output = command([
            "docker", "exec", self.observer_id, "/app/snapshot.sh", container_id
        ]).stdout
        return json.loads(output)

    @staticmethod
    def _contract(container_id: str, expected_cpus: tuple[int, ...]) -> dict[str, Any]:
        raw = command([
            "docker", "inspect", "--format", "{{json .HostConfig}}", container_id
        ]).stdout
        config = json.loads(raw)
        expected = {
            "CpusetCpus": cpuset(expected_cpus),
            "NanoCpus": len(expected_cpus) * 1_000_000_000,
            "Memory": MEMORY_BYTES,
            "MemorySwap": MEMORY_BYTES,
        }
        observed = {key: config.get(key) for key in expected}
        mismatches = [
            f"{key}={observed[key]!r}, expected {value!r}"
            for key, value in expected.items()
            if observed[key] != value
        ]
        return {"expected": expected, "observed": observed, "mismatches": mismatches}

    @staticmethod
    def _wait_event(container_id: str, event: str, timeout: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            logs = command(["docker", "logs", container_id], check=False)
            for line in reversed(logs.stdout.splitlines()):
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict) and value.get("event") == event:
                    return value
            state = command([
                "docker", "inspect", "--format", "{{.State.Status}}", container_id
            ], check=False).stdout.strip()
            if state == "exited":
                raise RuntimeError(
                    f"container exited while waiting for {event}: "
                    f"{logs.stdout}{logs.stderr}"
                )
            time.sleep(0.05)
        raise TimeoutError(f"timed out waiting for {event} from {container_id}")


def _resource_summary(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    completed: int,
    window: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    resource_elapsed = max(
        float(after["captured_monotonic"]) - float(before["captured_monotonic"]),
        1e-9,
    )
    measured_operations = completed + window
    result["measured_operations"] = measured_operations
    for role, cores in (("target", 1), ("partner", 4)):
        first = before[role]
        last = after[role]
        usage_usec = max(0, int(last["usage_usec"]) - int(first["usage_usec"]))
        user_usec = max(0, int(last["user_usec"]) - int(first["user_usec"]))
        system_usec = max(0, int(last["system_usec"]) - int(first["system_usec"]))
        result[f"{role}_cpu_s"] = usage_usec / 1_000_000
        result[f"{role}_user_cpu_s"] = user_usec / 1_000_000
        result[f"{role}_system_cpu_s"] = system_usec / 1_000_000
        result[f"{role}_cpu_fraction"] = usage_usec / (resource_elapsed * cores * 1_000_000)
        result[f"{role}_cpu_ns_per_operation"] = (
            usage_usec * 1000 / measured_operations if measured_operations else 0
        )
        result[f"{role}_user_cpu_ns_per_operation"] = (
            user_usec * 1000 / measured_operations if measured_operations else 0
        )
        result[f"{role}_system_cpu_ns_per_operation"] = (
            system_usec * 1000 / measured_operations if measured_operations else 0
        )
        result[f"{role}_rss_bytes"] = int(last["memory_current"])
        result[f"{role}_peak_memory_bytes"] = int(last["memory_peak"])
        result[f"{role}_throttled_periods"] = max(
            0, int(last["nr_throttled"]) - int(first["nr_throttled"])
        )
    result["resource_elapsed_seconds"] = resource_elapsed
    return result


def _safe(value: str) -> str:
    return "".join(character if character.isalnum() or character in "_.-" else "-" for character in value)
