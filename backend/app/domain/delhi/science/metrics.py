"""Pure metric functions for quantitative validation.

Every function computes a real metric from real numbers and refuses
inadequate input (empty/mismatched/non-finite) by raising ValueError —
the caller (validation engine) converts refusals into NOT_COMPUTABLE
with a reason. No function invents a value.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple


def _check_pairs(observed: Sequence[Optional[float]], predicted: Sequence[Optional[float]]) -> List[Tuple[float, float]]:
    """Pair observed/predicted values, dropping None pairs (documented
    alignment: a None on either side is UNKNOWN and contributes no pair —
    never a zero)."""
    if len(observed) != len(predicted):
        raise ValueError(
            f"observed ({len(observed)}) and predicted ({len(predicted)}) "
            "lengths differ"
        )
    pairs = []
    for o, p in zip(observed, predicted):
        if o is None or p is None:
            continue
        if not (math.isfinite(o) and math.isfinite(p)):
            continue
        pairs.append((o, p))
    if not pairs:
        raise ValueError("no valid observed/predicted pairs after alignment")
    return pairs


def mae(observed, predicted) -> float:
    pairs = _check_pairs(observed, predicted)
    return sum(abs(o - p) for o, p in pairs) / len(pairs)


def rmse(observed, predicted) -> float:
    pairs = _check_pairs(observed, predicted)
    return math.sqrt(sum((o - p) ** 2 for o, p in pairs) / len(pairs))


def bias(observed, predicted) -> float:
    """Mean error (predicted - observed)."""
    pairs = _check_pairs(observed, predicted)
    return sum(p - o for o, p in pairs) / len(pairs)


def correlation(observed, predicted) -> Optional[float]:
    pairs = _check_pairs(observed, predicted)
    n = len(pairs)
    if n < 3:
        return None  # correlation is not meaningful below 3 pairs
    mean_o = sum(o for o, _ in pairs) / n
    mean_p = sum(p for _, p in pairs) / n
    cov = sum((o - mean_o) * (p - mean_p) for o, p in pairs)
    var_o = sum((o - mean_o) ** 2 for o, _ in pairs)
    var_p = sum((p - mean_p) ** 2 for _, p in pairs)
    if var_o == 0 or var_p == 0:
        return None
    return cov / math.sqrt(var_o * var_p)


def peak_error(observed, predicted) -> Dict[str, Optional[float]]:
    """Absolute peak-magnitude error and time-to-peak error in steps.

    timing_error_steps is None when either series' peak is not unique
    enough to localize (first occurrence is used, documented).
    """
    pairs = _check_pairs(observed, predicted)
    o_vals = [o for o, _ in pairs]
    p_vals = [p for _, p in pairs]
    o_peak = max(o_vals)
    p_peak = max(p_vals)
    # First-occurrence index within the ORIGINAL series (None-skipping
    # would misalign timing; use the raw index space).
    o_idx = next(
        i for i, v in enumerate(observed) if v is not None and v == o_peak
    )
    p_idx = next(
        i for i, v in enumerate(predicted) if v is not None and v == p_peak
    )
    return {
        "peak_abs_error": abs(o_peak - p_peak),
        "peak_observed": o_peak,
        "peak_predicted": p_peak,
        "timing_error_steps": float(o_idx - p_idx),
    }


def nash_sutcliffe(observed, predicted) -> float:
    pairs = _check_pairs(observed, predicted)
    n = len(pairs)
    mean_o = sum(o for o, _ in pairs) / n
    denom = sum((o - mean_o) ** 2 for o, _ in pairs)
    if denom == 0:
        raise ValueError("NSE undefined: zero variance in observations")
    return 1.0 - sum((o - p) ** 2 for o, p in pairs) / denom


def kling_gupta(observed, predicted) -> Dict[str, float]:
    pairs = _check_pairs(observed, predicted)
    n = len(pairs)
    mean_o = sum(o for o, _ in pairs) / n
    mean_p = sum(p for _, p in pairs) / n
    var_o = sum((o - mean_o) ** 2 for o, _ in pairs)
    var_p = sum((p - mean_p) ** 2 for _, p in pairs)
    if var_o == 0 or var_p == 0:
        raise ValueError("KGE undefined: zero variance in observations")
    r = correlation(observed, predicted)
    alpha = math.sqrt(var_p / n) / math.sqrt(var_o / n)
    beta = mean_p / mean_o if mean_o != 0 else None
    if r is None or beta is None:
        raise ValueError("KGE undefined: degenerate correlation or mean")
    kge = math.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2)
    return {"kge": kge, "r": r, "alpha": alpha, "beta": beta}


def volume_error_fraction(observed, predicted) -> float:
    """(predicted_total - observed_total) / observed_total over pairs."""
    pairs = _check_pairs(observed, predicted)
    total_o = sum(o for o, _ in pairs)
    if total_o == 0:
        raise ValueError("volume error undefined: zero observed volume")
    return (sum(p for _, p in pairs) - total_o) / total_o


def confusion_matrix(
    observed_labels: List[Optional[bool]], predicted_labels: List[Optional[bool]]
) -> Dict[str, int]:
    """Binary confusion matrix. None on either side = UNKNOWN and is
    EXCLUDED (never counted as a negative — no FLOOD_NO invention)."""
    if len(observed_labels) != len(predicted_labels):
        raise ValueError("label length mismatch")
    cm = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "excluded_unknown": 0}
    for o, p in zip(observed_labels, predicted_labels):
        if o is None or p is None:
            cm["excluded_unknown"] += 1
            continue
        if o and p:
            cm["tp"] += 1
        elif not o and p:
            cm["fp"] += 1
        elif o and not p:
            cm["fn"] += 1
        else:
            cm["tn"] += 1
    if (cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"]) == 0:
        raise ValueError("no valid label pairs after UNKNOWN exclusion")
    return cm


def classification_metrics(observed_labels, predicted_labels) -> Dict[str, Optional[float]]:
    cm = confusion_matrix(observed_labels, predicted_labels)
    tp, fp, fn, tn = cm["tp"], cm["fp"], cm["fn"], cm["tn"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    specificity = tn / (tn + fp) if (tn + fp) > 0 else None
    balanced = (
        (recall + specificity) / 2 if recall is not None and specificity is not None else None
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "balanced_accuracy": balanced,
        "confusion_matrix": cm,
    }


def extent_metrics(observed_mask, predicted_mask) -> Dict[str, Optional[float]]:
    """Cell-wise inundation extent metrics (IoU/precision/recall/F1 and
    false area fractions). Masks are equal-length 0/1 sequences; None =
    UNKNOWN cell (excluded)."""
    if len(observed_mask) != len(predicted_mask):
        raise ValueError("mask length mismatch")
    inter = 0
    obs_only = 0
    pred_only = 0
    excluded = 0
    for o, p in zip(observed_mask, predicted_mask):
        if o is None or p is None:
            excluded += 1
            continue
        if o and p:
            inter += 1
        elif o and not p:
            obs_only += 1
        elif p and not o:
            pred_only += 1
    union = inter + obs_only + pred_only
    if union == 0:
        raise ValueError("extent metrics undefined: empty union after exclusions")
    precision = inter / (inter + pred_only) if (inter + pred_only) else None
    recall = inter / (inter + obs_only) if (inter + obs_only) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision and recall and (precision + recall) > 0
        else None
    )
    return {
        "iou": inter / union,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_area_fraction": pred_only / union,
        "false_negative_area_fraction": obs_only / union,
        "excluded_unknown_cells": excluded,
    }
