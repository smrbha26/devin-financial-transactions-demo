"""
Report generation module.

Generates a transaction-level risk report in CSV format.
"""

import csv
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATH = os.path.join("output", "transaction_risk_report.csv")
REPORT_FIELDS = ["transaction_id", "risk_score", "risk_category", "contributing_factors"]


def generate_report(
    results: list[dict[str, Any]],
    output_path: str = DEFAULT_OUTPUT_PATH,
) -> str:
    """Generate a CSV risk report from scored transaction results.

    Args:
        results: List of dicts with keys matching REPORT_FIELDS.
        output_path: File path for the output CSV.

    Returns:
        The absolute path of the generated report.

    Raises:
        ValueError: If results list is empty.
        OSError: If the output directory cannot be created.
    """
    if not results:
        raise ValueError("No results to write. Results list is empty.")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    abs_path = os.path.abspath(output_path)
    logger.info("Report generated with %d transactions at %s", len(results), abs_path)
    return abs_path
