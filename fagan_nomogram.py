#!/usr/bin/env python3
"""Fagan/Bayes diagnostic probability updater (percent-scale inputs).

All probabilities, sensitivity and specificity are percentages in [0, 100].
An explicit likelihood ratio is non-negative; an infinite LR can also result
from a perfectly specific positive test or perfectly sensitive negative test.
"""

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any


def _percentage(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number between 0 and 100") from exc
    if not math.isfinite(number) or not 0 <= number <= 100:
        raise ValueError(f"{name} must be a finite number between 0 and 100")
    return number


def _likelihood_ratio(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("likelihood_ratio must be a non-negative finite number") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError("likelihood_ratio must be a non-negative finite number")
    return number


def _json_number(value: float) -> float | str:
    """Represent infinite odds / LRs without emitting invalid JSON Infinity."""
    return "infinity" if math.isinf(value) else value


def calculate_metrics(
    *,
    pretest_probability: float,
    likelihood_ratio: float | None = None,
    sensitivity: float | None = None,
    specificity: float | None = None,
    result: str = "positive",
) -> dict[str, Any]:
    """Update a pre-test probability using a result-specific likelihood ratio.

    Specify either a direct ``likelihood_ratio`` or both ``sensitivity`` and
    ``specificity`` (all accuracy percentages on a 0--100 scale). The result
    selects LR+ or LR- when accuracy measures are supplied. A zero prior with
    infinite LR, or certain prior with zero LR, is mathematically undefined.
    """
    pretest = _percentage(pretest_probability, "pretest_probability")
    outcome = str(result).lower()
    if outcome not in {"positive", "negative"}:
        raise ValueError("result must be 'positive' or 'negative'")

    if likelihood_ratio is not None:
        if sensitivity is not None or specificity is not None:
            raise ValueError("provide either likelihood_ratio or sensitivity and specificity")
        lr = _likelihood_ratio(likelihood_ratio)
    else:
        if sensitivity is None or specificity is None:
            raise ValueError("provide likelihood_ratio or both sensitivity and specificity")
        sens = _percentage(sensitivity, "sensitivity") / 100
        spec = _percentage(specificity, "specificity") / 100
        numerator, denominator = (sens, 1 - spec) if outcome == "positive" else (1 - sens, spec)
        if numerator == 0 and denominator == 0:
            raise ValueError("likelihood ratio is undefined for this test result")
        lr = numerator / denominator if denominator else math.inf

    p = pretest / 100
    if (p == 0 and math.isinf(lr)) or (p == 1 and lr == 0):
        raise ValueError("posterior is undefined for this combination of prior and likelihood ratio")

    if p == 0 or lr == 0:
        posterior = 0.0
    elif p == 1 or math.isinf(lr):
        posterior = 1.0
    else:
        # Log odds avoids overflow for very large/small likelihood ratios.
        log_odds = math.log(p) - math.log1p(-p) + math.log(lr)
        posterior = (1 / (1 + math.exp(-log_odds))) if log_odds >= 0 else (
            math.exp(log_odds) / (1 + math.exp(log_odds))
        )

    prior_odds = p / (1 - p) if p < 1 else math.inf
    post_odds = posterior / (1 - posterior) if posterior < 1 else math.inf
    return {
        "pretest_probability": pretest,
        "test_result": outcome,
        "likelihood_ratio": _json_number(lr),
        "pretest_odds": _json_number(prior_odds),
        "posttest_odds": _json_number(post_odds),
        "posttest_probability": posterior * 100,
        "probability_change": posterior * 100 - pretest,
    }


def _resolve_safe_path(path_str: str, must_exist: bool = False) -> Path:
    """Normalize a CLI path and verify its input-file type when requested."""
    path = Path(path_str).expanduser().resolve()
    if must_exist and not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if must_exist and not path.is_file():
        raise ValueError(f"Input path is not a regular file: {path}")
    return path


def process_batch(input_csv: str, output_csv: str) -> None:
    """Atomically write Bayesian results for CSV rows with named inputs."""
    input_path = _resolve_safe_path(input_csv, must_exist=True)
    output_path = _resolve_safe_path(output_csv)
    if input_path == output_path:
        raise ValueError("Input and output paths must differ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_columns = ["likelihood_ratio", "pretest_odds", "posttest_odds", "posttest_probability", "probability_change"]
    temp_path: str | None = None
    try:
        with input_path.open(newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames or []
            if not fields:
                raise ValueError("CSV input has no header row")
            if len(fields) != len(set(fields)):
                raise ValueError("CSV input contains duplicate column names")
            if "pretest_probability" not in fields:
                raise ValueError("CSV requires pretest_probability column")
            if any(name in fields for name in result_columns[1:]):
                raise ValueError("CSV contains a reserved output column")
            if "likelihood_ratio" not in fields and not {"sensitivity", "specificity"}.issubset(fields):
                raise ValueError("CSV requires likelihood_ratio or sensitivity and specificity columns")
            fieldnames = fields + [name for name in result_columns if name not in fields]
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=output_path.parent,
                                             prefix=".fagan-", suffix=".csv", delete=False) as target:
                temp_path = target.name
                writer = csv.DictWriter(target, fieldnames=fieldnames)
                writer.writeheader()
                count = 0
                for row_number, row in enumerate(reader, start=2):
                    if None in row:
                        raise ValueError(f"CSV row {row_number} has extra columns")
                    try:
                        has_lr = row.get("likelihood_ratio", "") != ""
                        metrics = calculate_metrics(
                            pretest_probability=row["pretest_probability"],
                            likelihood_ratio=row["likelihood_ratio"] if has_lr else None,
                            sensitivity=None if has_lr else row.get("sensitivity"),
                            specificity=None if has_lr else row.get("specificity"),
                            result=row.get("result", "positive") or "positive",
                        )
                    except ValueError as exc:
                        raise ValueError(f"CSV row {row_number}: {exc}") from exc
                    writer.writerow({**row, **{key: metrics[key] for key in result_columns}})
                    count += 1
        os.replace(temp_path, output_path)
        temp_path = None
    finally:
        if temp_path is not None:
            Path(temp_path).unlink(missing_ok=True)
    print(f"Processed {count} records -> {output_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fagan nomogram: update diagnostic probability with Bayes' theorem")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Calculate one post-test probability")
    single.add_argument("--pretest", type=float, required=True, help="Pre-test probability, 0 to 100 percent")
    source = single.add_mutually_exclusive_group(required=True)
    source.add_argument("--lr", type=float, help="Likelihood ratio for the observed result")
    source.add_argument("--sensitivity", type=float, help="Test sensitivity in percent; requires --specificity")
    single.add_argument("--specificity", type=float, help="Test specificity in percent")
    single.add_argument("--result", choices=["positive", "negative"], default="positive")
    batch = commands.add_parser("batch", help="Calculate CSV records")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            if args.sensitivity is not None and args.specificity is None:
                parser.error("--sensitivity requires --specificity")
            if args.lr is not None and args.specificity is not None:
                parser.error("--specificity cannot be combined with --lr")
            result = calculate_metrics(pretest_probability=args.pretest, likelihood_ratio=args.lr,
                                       sensitivity=args.sensitivity, specificity=args.specificity,
                                       result=args.result)
            print(json.dumps(result, indent=2, allow_nan=False))
        else:
            process_batch(args.input, args.output)
    except (ValueError, OSError, csv.Error) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
