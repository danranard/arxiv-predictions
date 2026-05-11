from __future__ import annotations

import math
import statistics
from typing import Iterable


def metric_score(logprobs: Iterable[float], metric: str) -> float:
    values = list(logprobs)
    if not values:
        raise ValueError("metric_score requires at least one token logprob")
    if metric == "raw":
        return sum(values) / len(values)
    nll = [-value for value in values]
    if metric.startswith("clip"):
        cap = float(metric[4:])
        transformed = [-min(max(0.0, value), cap) for value in nll]
    elif metric == "sqrt_nll":
        transformed = [-math.sqrt(max(0.0, value)) for value in nll]
    elif metric == "log1p_nll":
        transformed = [-math.log1p(max(0.0, value)) for value in nll]
    else:
        raise ValueError(f"Unknown metric: {metric}")
    return sum(transformed) / len(transformed)


def summarize(values: Iterable[float]) -> dict[str, float | int | None]:
    xs = list(values)
    return {
        "n": len(xs),
        "mean": statistics.mean(xs) if xs else None,
        "stderr": statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else None,
        "median": statistics.median(xs) if xs else None,
        "positive_rate": sum(value > 0 for value in xs) / len(xs) if xs else None,
    }


def fmt(value: float | int | None, digits: int = 5, signed: bool = True) -> str:
    if value is None:
        return "NA"
    if isinstance(value, int):
        return str(value)
    prefix = "+" if signed else ""
    return f"{value:{prefix}.{digits}f}"

