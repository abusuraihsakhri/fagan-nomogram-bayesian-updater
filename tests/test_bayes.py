import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from fagan_nomogram import calculate_metrics, process_batch


def test_positive_and_negative_posteriors():
    positive = calculate_metrics(pretest_probability=30, sensitivity=90, specificity=80, result="positive")
    negative = calculate_metrics(pretest_probability=30, sensitivity=90, specificity=80, result="negative")
    assert positive["likelihood_ratio"] == pytest.approx(4.5)
    assert positive["posttest_probability"] == pytest.approx(65.85365853658537)
    assert negative["likelihood_ratio"] == pytest.approx(.125)
    assert negative["posttest_probability"] == pytest.approx(5.084745762711864)


def test_direct_lr_and_neutral_ratio():
    assert calculate_metrics(pretest_probability=20, likelihood_ratio=4)["posttest_probability"] == pytest.approx(50)
    assert calculate_metrics(pretest_probability=20, likelihood_ratio=1)["posttest_probability"] == pytest.approx(20)


@pytest.mark.parametrize("input_data", [
    {"pretest_probability": -1, "likelihood_ratio": 1},
    {"pretest_probability": 101, "likelihood_ratio": 1},
    {"pretest_probability": float("nan"), "likelihood_ratio": 1},
    {"pretest_probability": 20, "likelihood_ratio": -1},
    {"pretest_probability": 20, "likelihood_ratio": float("inf")},
    {"pretest_probability": 20, "sensitivity": 150, "specificity": 80},
    {"pretest_probability": 20, "sensitivity": 80, "specificity": 80, "result": "unknown"},
    {"pretest_probability": 20, "likelihood_ratio": 2, "sensitivity": 80, "specificity": 80},
    {"pretest_probability": 0, "sensitivity": 80, "specificity": 100},
    {"pretest_probability": 100, "likelihood_ratio": 0},
    {"pretest_probability": 20, "sensitivity": 0, "specificity": 100},
])
def test_invalid_inputs(input_data):
    with pytest.raises(ValueError):
        calculate_metrics(**input_data)


def test_endpoints_and_large_ratios():
    assert calculate_metrics(pretest_probability=0, likelihood_ratio=2)["posttest_probability"] == 0
    assert calculate_metrics(pretest_probability=100, likelihood_ratio=2)["posttest_probability"] == 100
    assert calculate_metrics(pretest_probability=20, sensitivity=80, specificity=100)["likelihood_ratio"] == "infinity"
    assert calculate_metrics(pretest_probability=20, sensitivity=80, specificity=100)["posttest_probability"] == 100
    assert calculate_metrics(pretest_probability=20, likelihood_ratio=1e300)["posttest_probability"] == 100
    assert calculate_metrics(pretest_probability=20, likelihood_ratio=1e-300)["posttest_probability"] >= 0


def test_batch_csv_and_rollback(tmp_path):
    inp = tmp_path / "input.csv"
    out = tmp_path / "results.csv"
    inp.write_text("study,pretest_probability,sensitivity,specificity,result\nA,30,90,80,positive\nB,30,90,80,negative\n")
    process_batch(str(inp), str(out))
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 2
    assert float(rows[0]["posttest_probability"]) == pytest.approx(65.85365853658537)
    assert float(rows[1]["posttest_probability"]) == pytest.approx(5.084745762711864)
    before = out.read_bytes()
    inp.write_text("pretest_probability,likelihood_ratio\n30,4\nBAD,-1\n")
    with pytest.raises(ValueError, match="CSV row 3"):
        process_batch(str(inp), str(out))
    assert out.read_bytes() == before
    assert list(tmp_path.glob(".fagan-*")) == []


def test_cli_json(tmp_path):
    module = Path(__file__).resolve().parent.parent / "fagan_nomogram.py"
    process = subprocess.run([sys.executable, str(module), "single", "--pretest", "30", "--lr", "4.5"],
                             capture_output=True, text=True, check=True)
    assert json.loads(process.stdout)["posttest_probability"] == pytest.approx(65.85365853658537)
