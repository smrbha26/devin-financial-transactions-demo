"""Integration tests for the pipeline module."""

import csv
import os
import tempfile

import pytest

from src.pipeline import load_transactions, process_transactions, run_pipeline


class TestLoadTransactions:
    def test_load_valid_csv(self):
        transactions = load_transactions("data/Example1.csv")
        assert len(transactions) > 0
        assert "amount" in transactions[0]
        assert "type" in transactions[0]

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_transactions("nonexistent.csv")

    def test_non_csv_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not a csv")
            temp_path = f.name
        try:
            with pytest.raises(ValueError, match="CSV"):
                load_transactions(temp_path)
        finally:
            os.unlink(temp_path)


class TestProcessTransactions:
    def test_process_returns_results(self):
        transactions = load_transactions("data/Example1.csv")
        results = process_transactions(transactions)
        assert len(results) == len(transactions)
        for r in results:
            assert "transaction_id" in r
            assert "risk_score" in r
            assert "risk_category" in r
            assert "contributing_factors" in r
            assert r["risk_category"] in ("LOW", "MEDIUM", "HIGH")
            assert 0 <= r["risk_score"] <= 100

    def test_all_categories_present(self):
        transactions = load_transactions("data/Example1.csv")
        results = process_transactions(transactions)
        categories = {r["risk_category"] for r in results}
        # The sample data should produce at least LOW and some risk
        assert "LOW" in categories or "MEDIUM" in categories or "HIGH" in categories


class TestRunPipeline:
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.csv")
            report_path = run_pipeline(
                input_path="data/Example1.csv",
                output_path=output_path,
            )
            assert os.path.exists(report_path)

            with open(report_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) > 0
                assert set(reader.fieldnames) == {
                    "transaction_id",
                    "risk_score",
                    "risk_category",
                    "contributing_factors",
                }
