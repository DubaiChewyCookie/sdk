from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, replace
from itertools import zip_longest
from typing import Iterable


LABEL = "io.dart.benchmark.secure-socket-buffer-size"


@dataclass(frozen=True)
class LogicalCpu:
    cpu: int
    package: int
    core: int
    siblings: tuple[int, ...]
    llc: str

    @property
    def physical_key(self) -> tuple[int, int]:
        return (self.package, self.core)


@dataclass(frozen=True)
class PhysicalCore:
    package: int
    core: int
    logical_cpu: int
    siblings: tuple[int, ...]
    llc: str

    @property
    def key(self) -> tuple[int, int]:
        return (self.package, self.core)


@dataclass(frozen=True)
class CpuPlacement:
    target_cpus: tuple[int, ...]
    partner_cpus: tuple[int, ...]
    observer_cpus: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Topology:
    logical_cpus: tuple[LogicalCpu, ...]
    physical_cores: tuple[PhysicalCore, ...]
    llc_source: str = "sysfs"

    def as_dict(self) -> dict[str, object]:
        logical = [asdict(item) for item in self.logical_cpus]
        physical = [asdict(item) for item in self.physical_cores]
        for item in (*logical, *physical):
            item["siblings"] = list(item["siblings"])
        return {
            "logical_cpu_count": len(logical),
            "physical_core_count": len(physical),
            "llc_groups": sorted({item.llc for item in self.physical_cores}),
            "llc_source": self.llc_source,
            "logical_cpus": logical,
            "selected_physical_cores": physical,
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if len(self.physical_cores) < 6:
            errors.append(
                "at least six physical cores are required for target, partner, and observer"
            )
        selected = [item.logical_cpu for item in self.physical_cores]
        for index, item in enumerate(self.physical_cores):
            if set(item.siblings).intersection(selected[index + 1 :]):
                errors.append(f"selected CPU {item.logical_cpu} shares an SMT sibling")
        return errors

    def placement(self, repetition: int) -> CpuPlacement:
        ordered = list(_interleave_llc(self.physical_cores))
        if len(ordered) < 6:
            raise ValueError("at least six physical cores are required")
        observer = ordered[0]
        available = ordered[1:]
        rotation = ((repetition - 1) * 5) % len(available)
        available = available[rotation:] + available[:rotation]
        result = CpuPlacement(
            observer_cpus=(observer.logical_cpu,),
            target_cpus=(available[0].logical_cpu,),
            partner_cpus=tuple(item.logical_cpu for item in available[1:5]),
        )
        sets = [set(result.observer_cpus), set(result.target_cpus), set(result.partner_cpus)]
        if any(sets[left] & sets[right] for left in range(3) for right in range(left + 1, 3)):
            raise AssertionError("observer, target, and partner CPU sets overlap")
        return result


def discover() -> Topology:
    script = r'''set -eu
for path in /sys/devices/system/cpu/cpu[0-9]*; do
  cpu=${path##*cpu}
  if [ -f "$path/online" ] && [ "$(cat "$path/online")" != "1" ]; then continue; fi
  package=$(cat "$path/topology/physical_package_id")
  core=$(cat "$path/topology/core_id")
  siblings=$(cat "$path/topology/thread_siblings_list")
  llc=""
  for cache in "$path"/cache/index*; do
    [ -d "$cache" ] || continue
    if [ "$(cat "$cache/level")" = "3" ]; then
      if [ -f "$cache/id" ]; then llc=$(cat "$cache/id"); else llc=$(cat "$cache/shared_cpu_list"); fi
      break
    fi
  done
  [ -n "$llc" ] || llc="package-$package"
  printf '%s|%s|%s|%s|%s\n' "$cpu" "$package" "$core" "$siblings" "$llc"
done'''
    completed = subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none", "--label",
            f"{LABEL}=true", "alpine:3.21", "sh", "-c", script,
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    logical: list[LogicalCpu] = []
    for line in completed.stdout.splitlines():
        cpu, package, core, siblings, llc = line.split("|", 4)
        logical.append(
            LogicalCpu(
                int(cpu), int(package), int(core), tuple(_parse_cpu_list(siblings)), llc
            )
        )
    logical.sort(key=lambda item: item.cpu)
    by_core: dict[tuple[int, int], list[LogicalCpu]] = {}
    for item in logical:
        by_core.setdefault(item.physical_key, []).append(item)
    llc_source = "sysfs"
    if len({item.llc for item in logical}) < 2 and len(by_core) == 16 and len(logical) == 32:
        inferred = {
            key: f"inferred-ccd-{index // 8}"
            for index, key in enumerate(sorted(by_core))
        }
        logical = [replace(item, llc=inferred[item.physical_key]) for item in logical]
        by_core = {}
        for item in logical:
            by_core.setdefault(item.physical_key, []).append(item)
        llc_source = "inferred_5950x_core_halves_due_wsl"
    physical = tuple(
        PhysicalCore(
            members[0].package,
            members[0].core,
            min(item.cpu for item in members),
            members[0].siblings,
            members[0].llc,
        )
        for _, members in sorted(by_core.items())
    )
    topology = Topology(tuple(logical), physical, llc_source)
    errors = topology.validate()
    if errors:
        raise RuntimeError("invalid Docker CPU topology: " + "; ".join(errors))
    return topology


def cpuset(cpus: Iterable[int]) -> str:
    return ",".join(str(cpu) for cpu in cpus)


def _parse_cpu_list(value: str) -> list[int]:
    result: list[int] = []
    for part in value.split(","):
        if "-" in part:
            first, last = (int(item) for item in part.split("-", 1))
            result.extend(range(first, last + 1))
        else:
            result.append(int(part))
    return result


def _interleave_llc(cores: Iterable[PhysicalCore]) -> tuple[PhysicalCore, ...]:
    groups: dict[str, list[PhysicalCore]] = {}
    for core in cores:
        groups.setdefault(core.llc, []).append(core)
    rows = [sorted(group, key=lambda item: item.key) for _, group in sorted(groups.items())]
    return tuple(item for row in zip_longest(*rows) for item in row if item is not None)
