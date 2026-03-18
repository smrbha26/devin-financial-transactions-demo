"""
Main fraud risk scoring pipeline.

Orchestrates reading input data, scoring transactions, classifying risk,
and generating the output report.
"""

import csv
import logging
import sys
from typing import Any

from src.classification import classify_risk
from src.report import DEFAULT_OUTPUT_PATH, generate_report
from src.scoring import compute_risk_score
from src.validation import validate_columns, validate_file_path, validate_transaction

logger = logging.getLogger(__name__)

DEFAULT_INPUT_PATH = "data/Example1.csv"


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_transactions(file_path: str) -> list[dict[str, Any]]:
    """Load and validate transactions from a CSV file.

    Args:
        file_path: Path to the input CSV.

    Returns:
        List of validated transaction dictionaries.
    """
    validate_file_path(file_path)

    transactions: list[dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row.")
        validate_columns(list(reader.fieldnames))

        for row_index, row in enumerate(reader, start=2):
            if validate_transaction(row, row_index):
                transactions.append(row)

    logger.info("Loaded %d valid transactions from %s", len(transactions), file_path)
    return transactions


def process_transactions(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score and classify all transactions.

    Tracks seen destinations and transaction counts across the dataset
    to support context-aware scoring rules.

    Args:
        transactions: List of validated transaction dicts.

    Returns:
        List of result dicts ready for report generation.
    """
    seen_destinations: set[str] = set()
    transaction_counts: dict[str, int] = {}
    results: list[dict[str, Any]] = []

    for idx, tx in enumerate(transactions, start=1):
        orig_name = str(tx["nameOrig"])
        dest_name = str(tx["nameDest"])

        # Update transaction count for originator
        transaction_counts[orig_name] = transaction_counts.get(orig_name, 0) + 1

        # Compute risk score
        risk_score, factors = compute_risk_score(tx, seen_destinations, transaction_counts)

        # Classify risk
        risk_category = classify_risk(risk_score)

        # Build result row
        result = {
            "transaction_id": f"TXN-{idx:05d}",
            "risk_score": risk_score,
            "risk_category": risk_category,
            "contributing_factors": "; ".join(factors),
        }
        results.append(result)

        # Mark destination as seen after scoring
        seen_destinations.add(dest_name)

    logger.info(
        "Processed %d transactions: %d LOW, %d MEDIUM, %d HIGH",
        len(results),
        sum(1 for r in results if r["risk_category"] == "LOW"),
        sum(1 for r in results if r["risk_category"] == "MEDIUM"),
        sum(1 for r in results if r["risk_category"] == "HIGH"),
    )

    return results


def run_pipeline(
    input_path: str = DEFAULT_INPUT_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH,
    verbose: bool = False,
) -> str:
    """Execute the full fraud risk scoring pipeline.

    Args:
        input_path: Path to input transaction CSV.
        output_path: Path for the output risk report CSV.
        verbose: Enable debug-level logging.

    Returns:
        Path to the generated report.
    """
    setup_logging(verbose)
    logger.info("Starting fraud risk scoring pipeline")
    logger.info("Input: %s", input_path)
    logger.info("Output: %s", output_path)

    transactions = load_transactions(input_path)

    if not transactions:
        logger.warning("No valid transactions found. Exiting.")
        return ""

    results = process_transactions(transactions)
    report_path = generate_report(results, output_path)

    logger.info("Pipeline completed successfully. Report: %s", report_path)
    return report_path


def main() -> None:
    """CLI entry point for the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fraud Risk Scoring Pipeline"
    )
    parser.add_argument(
        "-i", "--input",
        default=DEFAULT_INPUT_PATH,
        help=f"Path to input CSV file (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path for output report CSV (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging",
    )
    args = parser.parse_args()

    try:
        report_path = run_pipeline(args.input, args.output, args.verbose)
        if report_path:
            print(f"\nReport generated: {report_path}")
        else:
            print("\nNo report generated (no valid transactions).")
            sys.exit(1)
    except (FileNotFoundError, ValueError) as e:
        logger.error("Pipeline failed: %s", e)
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error in pipeline")
        sys.exit(1)


if __name__ == "__main__":
    main()
