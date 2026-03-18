"""
Input validation module.

Validates transaction data before processing.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
}


def validate_file_path(file_path: str) -> None:
    """Validate that the input file exists and is a CSV.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a CSV.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    if not file_path.lower().endswith(".csv"):
        raise ValueError(f"Input file must be a CSV file, got: {file_path}")


def validate_columns(columns: list[str]) -> None:
    """Validate that the CSV contains all required columns.

    Raises:
        ValueError: If required columns are missing.
    """
    column_set = {col.strip() for col in columns}
    missing = REQUIRED_COLUMNS - column_set
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def validate_transaction(transaction: dict[str, Any], row_index: int) -> bool:
    """Validate a single transaction row.

    Returns:
        True if the transaction is valid, False otherwise.
    """
    try:
        amount = float(transaction.get("amount", ""))
        if amount < 0:
            logger.warning("Row %d: Negative amount (%.2f), skipping.", row_index, amount)
            return False
    except (ValueError, TypeError):
        logger.warning("Row %d: Invalid amount value '%s', skipping.", row_index, transaction.get("amount"))
        return False

    tx_type = str(transaction.get("type", "")).strip()
    if not tx_type:
        logger.warning("Row %d: Missing transaction type, skipping.", row_index)
        return False

    orig_name = str(transaction.get("nameOrig", "")).strip()
    dest_name = str(transaction.get("nameDest", "")).strip()
    if not orig_name or not dest_name:
        logger.warning("Row %d: Missing account names, skipping.", row_index)
        return False

    try:
        float(transaction.get("oldbalanceOrg", 0))
        float(transaction.get("newbalanceOrig", 0))
    except (ValueError, TypeError):
        logger.warning("Row %d: Invalid balance values, skipping.", row_index)
        return False

    return True
