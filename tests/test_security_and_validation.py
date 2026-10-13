"""
Security and input validation tests for fagan-nomogram-bayesian-updater.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fagan_nomogram import calculate_metrics, process_batch, _resolve_safe_path
from agents.base import AuditTrail, PHIGuard, SecurityException


class TestResolveSafePath:
    def test_existing_file_resolves(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_text("a,b\n1,2\n")
        result = _resolve_safe_path(str(f), must_exist=True)
        assert result == f.resolve()

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _resolve_safe_path(str(tmp_path / "nonexistent.csv"), must_exist=True)

    def test_directory_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not a regular file"):
            _resolve_safe_path(str(tmp_path), must_exist=True)


class TestProcessBatchValidation:
    def test_same_input_output_raises(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_text("a,b\n1,2\n")
        with pytest.raises(ValueError, match="must differ"):
            process_batch(str(f), str(f))

    def test_missing_input_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "missing.csv"), str(tmp_path / "out.csv"))

    def test_empty_csv_raises(self, tmp_path):
        csv_in = tmp_path / "empty.csv"
        csv_in.write_text("")
        csv_out = tmp_path / "out.csv"
        with pytest.raises(ValueError, match="no header"):
            process_batch(str(csv_in), str(csv_out))

    def test_creates_output_directory(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_in.write_text("pretest_probability,likelihood_ratio\n10.0,5.0\n")
        csv_out = tmp_path / "subdir" / "nested" / "out.csv"
        process_batch(str(csv_in), str(csv_out))
        assert csv_out.exists()


class TestHMACIntegrity:
    def test_audit_trail_verifies_with_key(self):
        os.environ["AUDIT_SECRET_KEY"] = "test-key-for-integrity-verification"
        trail = AuditTrail()
        trail.log("tester", "unit", "TEST_EVENT", {"data": "value1"})
        trail.log("tester", "unit", "TEST_EVENT", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_trail_detects_tampering(self):
        os.environ["AUDIT_SECRET_KEY"] = "test-key-tamper-detection"
        trail = AuditTrail()
        trail.log("tester", "unit", "TEST_EVENT", {"data": "original"})
        # Tamper with the stored hash
        trail.logs[0]["current_hash"] = "TAMPERED_HASH_0000000000000000"
        assert trail.verify_integrity() is False


class TestPHIGuardRedaction:
    def test_redact_phi_mrn(self):
        result = PHIGuard.redact_phi("Patient MRN-12345678 has fever")
        assert "MRN-12345678" not in result
        assert "[REDACTED_IDENTIFIER]" in result

    def test_redact_phi_ssn(self):
        result = PHIGuard.redact_phi("SSN: 123-45-6789 confirmed")
        assert "123-45-6789" not in result

    def test_clean_text_unchanged(self):
        result = PHIGuard.redact_phi("Specimen KEY-001 optimal")
        assert result == "Specimen KEY-001 optimal"
