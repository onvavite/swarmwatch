"""Log schema: one JSON object per line (JSONL).

An event is the only thing the monitor ever sees — no agent internals,
no declared intent, only the trace. Fields:

- ts: ISO-8601 timestamp (UTC, e.g. 2026-11-06T14:00:00Z)
- agent: declared agent id (untrusted — agents may rename, see detector 2)
- channel: resource the event touches (file path, directory, chat room…)
- action: read | write | send | tool_call
- content: short text payload / tool arguments (may be falsified)
- declared: list of channels this agent declared at registration time
  (the monitor knows the declarations, not whether they are honoured)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

ACTIONS = {"read", "write", "send", "tool_call"}


@dataclass(frozen=True)
class Event:
    ts: str
    agent: str
    channel: str
    action: str
    content: str = ""
    declared: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        d = {
            "ts": self.ts,
            "agent": self.agent,
            "channel": self.channel,
            "action": self.action,
            "content": self.content,
        }
        if self.declared:
            d["declared"] = list(self.declared)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        missing = [k for k in ("ts", "agent", "channel", "action") if k not in d]
        if missing:
            raise ValueError(f"event missing fields: {missing}")
        if d["action"] not in ACTIONS:
            raise ValueError(f"unknown action: {d['action']!r}")
        declared = tuple(d.get("declared") or [])
        return cls(
            ts=str(d["ts"]),
            agent=str(d["agent"]),
            channel=str(d["channel"]),
            action=str(d["action"]),
            content=str(d.get("content") or ""),
            declared=declared,
        )


def load_jsonl(path: str) -> list[Event]:
    events: list[Event] = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(Event.from_dict(json.loads(line)))
            except (ValueError, json.JSONDecodeError) as e:
                raise ValueError(f"{path}:{i}: {e}") from e
    return events


def dump_jsonl(events: list[Event], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
