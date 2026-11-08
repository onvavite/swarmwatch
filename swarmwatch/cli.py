"""SwarmWatch CLI (stdlib only — zero heavy dependency).

Usage:
  python -m swarmwatch.cli generate hidden --seed 7 --out examples/hidden.jsonl
  python -m swarmwatch.cli generate control --seed 7 --out examples/control.jsonl
  python -m swarmwatch.cli detect examples/hidden.jsonl
  python -m swarmwatch.cli evaluate
"""

from __future__ import annotations

import argparse
import json
import sys

from .detectors import (detect_identity_churn, detect_shared_channel,
                        detect_split_task)
from .evaluate import evaluate
from .generator import generate
from .schema import dump_jsonl, load_jsonl


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="swarmwatch")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("kind", choices=["hidden", "control", "churn",
                                    "churn_control", "split", "split_control"])
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--agents", type=int, default=8)
    g.add_argument("--out", required=True)

    d = sub.add_parser("detect")
    d.add_argument("logfile")

    sub.add_parser("evaluate")

    args = p.parse_args(argv)
    if args.cmd == "generate":
        sc = generate(args.kind, n_agents=args.agents, seed=args.seed)
        dump_jsonl(sc.events, args.out)
        print(f"{args.kind}: {len(sc.events)} events -> {args.out}")
        if sc.hidden_channel:
            print(f"ground truth (not in log): {sc.hidden_channel} "
                  f"used by {', '.join(sc.hidden_agents)}")
        if sc.churn_ids:
            print(f"ground truth (not in log): churn {sc.churn_ids[0]} "
                  f"-> {sc.churn_ids[1]}")
        if sc.split_agents:
            print(f"ground truth (not in log): split parts held by "
                  f"{', '.join(sc.split_agents)}")
        return 0
    if args.cmd == "detect":
        events = load_jsonl(args.logfile)
        out = {
            "shared_channel": [f.to_dict()
                               for f in detect_shared_channel(events)],
            "identity_churn": [f.to_dict()
                               for f in detect_identity_churn(events)],
            "split_task": [f.to_dict()
                           for f in detect_split_task(events)],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if any(out.values()) else 1
    if args.cmd == "evaluate":
        print(json.dumps(evaluate().to_dict(), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
