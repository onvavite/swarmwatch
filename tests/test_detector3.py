"""Tests for detector 3 (split-task bypass). Run: python -m unittest discover -s tests -v"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from swarmwatch.detectors import detect_split_task  # noqa: E402
from swarmwatch.generator import generate  # noqa: E402
from swarmwatch.schema import Event  # noqa: E402


def _ev(ts, agent, content):
    return Event(ts=ts, agent=agent, channel="#tasks", action="write",
                 content=content, declared=("#tasks",))


class TestDetector3(unittest.TestCase):
    def test_split_scenario_flagged(self):
        for seed in range(10):
            sc = generate("split", seed=seed)
            findings = detect_split_task(sc.events)
            self.assertEqual(len(findings), 1,
                             f"expected 1 split finding, seed {seed}")
            self.assertEqual(findings[0].n_parts, 3)
            self.assertEqual(sorted(findings[0].parts_by_agent),
                             sorted(sc.split_agents))

    def test_split_control_clean(self):
        # One agent holds all three parts: single-agent attempt, no split.
        for seed in range(10):
            sc = generate("split_control", seed=seed)
            self.assertEqual(detect_split_task(sc.events), [],
                             f"false positive on split_control seed {seed}")

    def test_control_clean(self):
        for seed in range(10):
            sc = generate("control", seed=seed)
            self.assertEqual(detect_split_task(sc.events), [],
                             f"false positive on control seed {seed}")

    def test_incomplete_set_not_flagged(self):
        evs = [
            _ev("2026-11-06T14:00:00Z", "agent-00", "part 1/3: alpha"),
            _ev("2026-11-06T14:01:00Z", "agent-01", "part 2/3: beta"),
        ]
        self.assertEqual(detect_split_task(evs), [])

    def test_two_agents_split_flagged(self):
        evs = [
            _ev("2026-11-06T14:00:00Z", "agent-00", "part 1/3: alpha"),
            _ev("2026-11-06T14:01:00Z", "agent-01", "part 2/3: beta"),
            _ev("2026-11-06T14:02:00Z", "agent-01", "part 3/3: gamma"),
        ]
        findings = detect_split_task(evs)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].parts_by_agent,
                         {"agent-00": [1], "agent-01": [2, 3]})

    def test_hidden_scenario_not_flagged_as_split(self):
        # In hidden logs every conspirator holds all parts over rounds,
        # so no single-agent-full-set rule may fire: it is a shared
        # channel case (detector 1), not a split.
        for seed in range(10):
            sc = generate("hidden", seed=seed)
            self.assertEqual(detect_split_task(sc.events), [],
                             f"split false positive on hidden seed {seed}")


if __name__ == "__main__":
    unittest.main()
