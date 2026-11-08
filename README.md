# SwarmWatch — forensic monitor for swarm logs

**Swarm Alignment Hackathon, 6–8 Nov 2026 — Track 4: Multi-Agent Oversight and Control.**
Solo entry by Onvavite (@onvavite).

Question: can a monitor that only sees logs detect hidden coordination
between agents — even when agents rename, copy, or falsify their traces?

## Prior-work declaration (hackathon rule)

All code in this repo was written during the sprint weekend (from Fri 6 Nov
2026). Nothing pre-dates the sprint; the concept and plan (2 Nov) are
preparation only, not judged work.

## What it does

Inputs: JSONL logs, one event per line (`agent`, `ts`, `channel`, `action`,
`content`, plus each agent's declared channels). No agent internals.

Three detectors (all three implemented and measured):

1. **Shared undeclared channel** — several agents converge on a resource
   none of them declared (file, directory, room). Agent ↔ channel graph,
   flagged iff ≥ 2 agents and ≥ 4 events on the same undeclared channel.
   Score = agents × log10(events), with verbatim evidence excerpts.
2. **Identity churn** — rename/copy chains resolved by behavioural
   fingerprint (the signature marker stamped on an agent's ordinary
   messages, which travels with the entity, not the declared id), not
   by declared name. Flagged iff ≥ 2 ids share one marker with
   sequential, non-overlapping activity windows (a handoff); overlapping
   windows are two live agents, not a rename. Honest limit: a marker
   can be copied or dropped — the finding reports corroborating signals
   (shared dominant action/channel, handoff gap) alongside the match.
3. **Split-task bypass** — a refused task realised once split across
   agents: numbered parts ("part k/N") that together complete the
   sequence, spread across ≥ 2 agents, with no single agent holding the
   full set. One agent holding all parts is a single-agent attempt and
   is not flagged.

## Use (stdlib only, no install)

```bash
python -m swarmwatch.cli generate hidden --seed 7 --out examples/hidden.jsonl
python -m swarmwatch.cli generate control --seed 7 --out examples/control.jsonl
python -m swarmwatch.cli generate churn --seed 7 --out examples/churn.jsonl
python -m swarmwatch.cli generate split --seed 7 --out examples/split.jsonl
python -m swarmwatch.cli detect examples/hidden.jsonl   # all 3 detectors
python -m swarmwatch.cli evaluate                        # measured metrics
python -m unittest discover -s tests -v                  # 17 tests
```

## Friday results (measured, 6 Nov 2026)

Measured 6 Nov 2026 (`results/friday_eval.json`, produced by
`swarmwatch evaluate` on 20 hidden + 20 control synthetic scenarios,
fresh seeds): detector 1 — **recall 1.0 (20/20), 0 false positives,
precision 1.0**; naive keyword baseline — **recall 0.0 (0/20)**, because
the hidden fragments use neutral wording and content matching cannot
see them. The detector is content-agnostic: it only sees who meets
where. Honest limit: these are synthetic logs; real-world validation
(sample public: Swarm Traces / AI Village) is a Saturday stretch goal,
reported as-is if attempted.

## Saturday results (measured, 7 Nov 2026)

Measured 7 Nov 2026 (`results/saturday_eval.json`, `swarmwatch
evaluate`, 20 scenarios per class, fresh seeds) — all three detectors,
no regression on detector 1:

| detector | recall | false-positive rate |
|---|---|---|
| 1 — shared channel | 1.0 (20/20) | 0.0 (0/20) |
| 2 — identity churn | 1.0 (20/20) | 0.0 (0/20 controls) |
| 3 — split-task bypass | 1.0 (20/20) | 0.0 (0/20 controls) |
| baseline keyword | 0.0 (0/20) | 0.0 |

17 unit tests pass (`python -m unittest discover -s tests -v`), covering
each detector's positive case, its control case, and edge cases (lone
stray read, overlapping windows, incomplete part set, single agent
holding all parts). Remaining for Sunday 8 Nov: report PDF (official
template, 150–250-word abstract, Limitations + Dual-Use appendix),
submission before 23:59 AoE.

## Costs

0 $. Synthetic logs only, no GPU, no paid model. Evaluation is
deterministic and replayable by the judges from the provided logs.
