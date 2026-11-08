"""Evaluation: detector 1 vs baselines on synthetic scenarios.

Generates N hidden + N control scenarios (fresh seeds), runs the
detector and both baselines, and reports precision / recall / false
positive rate. All numbers are measured here — nothing is hard-coded.
A control log flagged by the detector counts as a false positive;
a hidden log with no finding counts as a false negative.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .detectors import (baseline_keyword, detect_identity_churn,
                        detect_shared_channel, detect_split_task)
from .generator import generate


@dataclass
class EvalResult:
    n_hidden: int
    n_control: int
    detector_tp: int
    detector_fp: int
    keyword_tp: int
    keyword_fp: int
    churn_tp: int = 0
    churn_fp: int = 0
    split_tp: int = 0
    split_fp: int = 0
    n_churn: int = 0
    n_split: int = 0

    @property
    def detector_recall(self) -> float:
        return self.detector_tp / self.n_hidden if self.n_hidden else 0.0

    @property
    def detector_fpr(self) -> float:
        return self.detector_fp / self.n_control if self.n_control else 0.0

    @property
    def detector_precision(self) -> float:
        d = self.detector_tp + self.detector_fp
        return self.detector_tp / d if d else 1.0

    @property
    def keyword_recall(self) -> float:
        return self.keyword_tp / self.n_hidden if self.n_hidden else 0.0

    @property
    def keyword_fpr(self) -> float:
        return self.keyword_fp / self.n_control if self.n_control else 0.0

    @property
    def churn_recall(self) -> float:
        return self.churn_tp / self.n_churn if self.n_churn else 0.0

    @property
    def churn_fpr(self) -> float:
        return self.churn_fp / self.n_churn if self.n_churn else 0.0

    @property
    def split_recall(self) -> float:
        return self.split_tp / self.n_split if self.n_split else 0.0

    @property
    def split_fpr(self) -> float:
        return self.split_fp / self.n_split if self.n_split else 0.0

    def to_dict(self) -> dict:
        return {
            "n_hidden": self.n_hidden,
            "n_control": self.n_control,
            "detector": {
                "true_positives": self.detector_tp,
                "false_positives": self.detector_fp,
                "recall": round(self.detector_recall, 3),
                "false_positive_rate": round(self.detector_fpr, 3),
                "precision": round(self.detector_precision, 3),
            },
            "baseline_keyword": {
                "true_positives": self.keyword_tp,
                "false_positives": self.keyword_fp,
                "recall": round(self.keyword_recall, 3),
                "false_positive_rate": round(self.keyword_fpr, 3),
            },
            "detector_churn": {
                "n_scenarios": self.n_churn,
                "true_positives": self.churn_tp,
                "false_positives": self.churn_fp,
                "recall": round(self.churn_recall, 3),
                "false_positive_rate": round(self.churn_fpr, 3),
            },
            "detector_split": {
                "n_scenarios": self.n_split,
                "true_positives": self.split_tp,
                "false_positives": self.split_fp,
                "recall": round(self.split_recall, 3),
                "false_positive_rate": round(self.split_fpr, 3),
            },
        }


def evaluate(n_per_class: int = 20, seed_base: int = 1000) -> EvalResult:
    tp = fp = ktp = kfp = 0
    for i in range(n_per_class):
        hidden = generate("hidden", seed=seed_base + i)
        if detect_shared_channel(hidden.events):
            tp += 1
        if baseline_keyword(hidden.events):
            ktp += 1
        control = generate("control", seed=seed_base + 500 + i)
        if detect_shared_channel(control.events):
            fp += 1
        if baseline_keyword(control.events):
            kfp += 1
    ctp = cfp = stp = sfp = 0
    for i in range(n_per_class):
        churn = generate("churn", seed=seed_base + 2000 + i)
        if detect_identity_churn(churn.events):
            ctp += 1
        churn_ctrl = generate("churn_control", seed=seed_base + 2500 + i)
        if detect_identity_churn(churn_ctrl.events):
            cfp += 1
        split = generate("split", seed=seed_base + 3000 + i)
        if detect_split_task(split.events):
            stp += 1
        split_ctrl = generate("split_control", seed=seed_base + 3500 + i)
        if detect_split_task(split_ctrl.events):
            sfp += 1
    return EvalResult(n_hidden=n_per_class, n_control=n_per_class,
                      detector_tp=tp, detector_fp=fp,
                      keyword_tp=ktp, keyword_fp=kfp,
                      churn_tp=ctp, churn_fp=cfp,
                      split_tp=stp, split_fp=sfp,
                      n_churn=n_per_class, n_split=n_per_class)


def main() -> None:
    result = evaluate()
    print(json.dumps(result.to_dict(), indent=2))
