import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from topology import LogicalCpu, PhysicalCore, Topology


def topology() -> Topology:
    logical = []
    physical = []
    for core in range(16):
        siblings = (core * 2, core * 2 + 1)
        llc = f"ccd-{core // 8}"
        logical.extend(LogicalCpu(cpu, 0, core, siblings, llc) for cpu in siblings)
        physical.append(PhysicalCore(0, core, siblings[0], siblings, llc))
    return Topology(tuple(logical), tuple(physical))


class TopologyTest(unittest.TestCase):
    def test_disjoint_physical_core_contract(self) -> None:
        value = topology()
        self.assertEqual([], value.validate())
        observer_sets = []
        for repetition in (1, 2):
            placement = value.placement(repetition)
            self.assertEqual(1, len(placement.target_cpus))
            self.assertEqual(4, len(placement.partner_cpus))
            self.assertEqual(1, len(placement.observer_cpus))
            self.assertFalse(set(placement.target_cpus) & set(placement.partner_cpus))
            self.assertFalse(set(placement.observer_cpus) & set(placement.target_cpus))
            self.assertFalse(set(placement.observer_cpus) & set(placement.partner_cpus))
            observer_sets.append(placement.observer_cpus)
        self.assertEqual(observer_sets[0], observer_sets[1])


if __name__ == "__main__":
    unittest.main()
