"""Tests for detector 2 (identity churn). Run: python -m unittest discover -s tests -v"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from swarmwatch.detectors import detect_identity_churn  # noqa: E402
from swarmwatch.generator import generate  # noqa: E402
from swarmwatch.schema import Event  # noqa: E402


def _ev(ts, agent, content, action="send"):
    return Event(ts=ts, agent=agent, channel="#general", action=action,
                 content=content, declared=("#general",))


class TestDetector2(unittest.TestCase):
    def test_churn_scenario_flagged(self):
        for seed in range(10):
            sc = generate("churn", seed=seed)
            findings = detect_identity_churn(sc.events)
            self.assertEqual(len(findings), 1,
                             f"expected 1 churn finding, seed {seed}")
            self.assertEqual(tuple(findings[0].ids),
                             tuple(sorted(sc.churn_ids,
                                          key=lambda a: min(
                                              e.ts for e in sc.events
                                              if e.agent == a))))

    def test_churn_control_clean(self):
        for seed in range(10):
            sc = generate("churn_control", seed=seed)
            self.assertEqual(detect_identity_churn(sc.events), [],
                             f"false positive on churn_control seed {seed}")

    def test_control_clean(self):
        for seed in range(10):
            sc = generate("control", seed=seed)
            self.assertEqual(detect_identity_churn(sc.events), [],
                             f"false positive on control seed {seed}")

    def test_overlapping_windows_not_flagged(self):
        # Same marker under two ids, but both active at the same time:
        # two live agents sharing a template, not a rename.
        evs = [
            _ev("2026-11-06T14:00:00Z", "agent-00", "status [quill]"),
            _ev("2026-11-06T14:01:00Z", "agent-01", "status [quill]"),
            _ev("2026-11-06T14:02:00Z", "agent-00", "review [quill]"),
            _ev("2026-11-06T14:03:00Z", "agent-01", "review [quill]"),
        ]
        self.assertEqual(detect_identity_churn(evs), [])

    def test_sequential_handoff_flagged(self):
        evs = [
            _ev("2026-11-06T14:00:00Z", "agent-00", "status [quill]"),
            _ev("2026-11-06T14:01:00Z", "agent-00", "review [quill]"),
            _ev("2026-11-06T14:02:00Z", "agent-09", "status [quill]"),
            _ev("2026-11-06T14:03:00Z", "agent-09", "review [quill]"),
        ]
        findings = detect_identity_churn(evs)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].ids, ["agent-00", "agent-09"])
        self.assertEqual(findings[0].token, "quill")

    def test_single_id_never_flagged(self):
        evs = [_ev(f"2026-11-06T14:0{i}:00Z", "agent-00", "status [quill]")
               for i in range(4)]
        self.assertEqual(detect_identity_churn(evs), [])


if __name__ == "__main__":
    unittest.main()
