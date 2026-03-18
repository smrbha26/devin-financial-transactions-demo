"""Unit tests for the risk classification module."""

import pytest

from src.classification import classify_risk


class TestClassifyRisk:
    def test_low_risk(self):
        assert classify_risk(0) == "LOW"
        assert classify_risk(10) == "LOW"
        assert classify_risk(39) == "LOW"
        assert classify_risk(39.99) == "LOW"

    def test_medium_risk(self):
        assert classify_risk(40) == "MEDIUM"
        assert classify_risk(55) == "MEDIUM"
        assert classify_risk(70) == "MEDIUM"

    def test_high_risk(self):
        assert classify_risk(70.01) == "HIGH"
        assert classify_risk(71) == "HIGH"
        assert classify_risk(85) == "HIGH"
        assert classify_risk(100) == "HIGH"

    # Edge cases at exact boundaries
    def test_boundary_at_40(self):
        assert classify_risk(39.99) == "LOW"
        assert classify_risk(40) == "MEDIUM"
        assert classify_risk(40.01) == "MEDIUM"

    def test_boundary_at_70(self):
        assert classify_risk(69.99) == "MEDIUM"
        assert classify_risk(70) == "MEDIUM"
        assert classify_risk(70.01) == "HIGH"

    def test_exact_zero(self):
        assert classify_risk(0) == "LOW"

    def test_exact_100(self):
        assert classify_risk(100) == "HIGH"

    def test_invalid_score_negative(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            classify_risk(-1)

    def test_invalid_score_over_100(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            classify_risk(101)
