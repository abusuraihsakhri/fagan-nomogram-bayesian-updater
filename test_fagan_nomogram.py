"""Smoke tests for the public Fagan API."""
import pytest
from fagan_nomogram import calculate_metrics, process_batch


def test_fagan_nomogram_single():
    res = calculate_metrics(pretest_probability=12, likelihood_ratio=4)
    assert res["posttest_probability"] == pytest.approx(35.294117647058826)


def test_fagan_nomogram_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("study,pretest_probability,likelihood_ratio\nA,15,3\nB,5,1\n", encoding="utf-8")
    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "A" in content
    assert "posttest_probability" in content
