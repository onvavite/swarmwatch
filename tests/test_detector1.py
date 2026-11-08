"""Tests for detector 1 (shared undeclared channel). Run: python -m unittest discover -s tests -v"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from swarmwatch.detectors import detect_shared_channel  # noqa: E402
from swarmwatch.generator import generate  # noqa: E402
from swarmwatch.schema import Event  # noqa: E402


class TestDetector1(unittest.TestCase):
    def test_hidden_scenario_flagged(self):
        sc = generate("hidden", seed=42)
        findings = detect_shared_channel(sc.events)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].channel, sc.hidden_channel)
        self.assertEqual(findings[0].agents, sorted(sc.hidden_agents))

    def test_control_scenario_clean(self):
        for seed in range(10):
            sc = generate("control", seed=seed)
            self.assertEqual(detect_shared_channel(sc.events), [],
                             f"false positive on control seed {seed}")

    def test_lone_stray_read_not_flagged(self):
        # One agent, one undeclared channel, one event: not coordination.
        evs = [Event(ts="2026-11-06T14:00:00Z", agent="agent-00",
                     channel="/tmp/.sync", action="read",
                     content="checking stray file", declared=("#general",))]
        self.assertEqual(detect_shared_channel(evs), [])

    def test_two_agents_few_events_not_flagged(self):
        # Two agents but only 2 events: below MIN_EVENTS, no flag.
        evs = [
            Event(ts="2026-11-06T14:00:00Z", agent="agent-00",
                  channel="/tmp/.sync", action="write", content="x",
                  declared=("#general",)),
            Event(ts="2026-11-06T14:01:00Z", agent="agent-01",
                  channel="/tmp/.sync", action="read", content="x",
                  declared=("#tasks",)),
        ]
        self.assertEqual(detect_shared_channel(evs), [])

    def test_declared_channel_never_flagged(self):
        # Heavy traffic on a declared channel is normal work, not hidden.
        evs = [
            Event(ts=f"2026-11-06T14:{i:02d}:00Z", agent=f"agent-{i % 3:02d}",
                  channel="#general", action="send", content="hello",
                  declared=("#general", "#tasks"))
            for i in range(20)
        ]
        self.assertEqual(detect_shared_channel(evs), [])


if __name__ == "__main__":
    unittest.main()
