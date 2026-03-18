"""
Fraud risk scoring module.

Computes a risk score (0-100) for each transaction using a rule-based approach.
Each scoring rule returns a weighted contribution, and the final score is
normalized to the 0-100 range.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Transaction amount thresholds
HIGH_AMOUNT_THRESHOLD = 10_000
VERY_HIGH_AMOUNT_THRESHOLD = 200_000

# High-risk transaction types
HIGH_RISK_TYPES = {"CASH_OUT", "TRANSFER"}

# Scoring weights (sum to 100 for easy reasoning)
WEIGHT_HIGH_AMOUNT = 25
WEIGHT_TRANSACTION_TYPE = 20
WEIGHT_BALANCE_ZEROED = 15
WEIGHT_NEW_DESTINATION = 15
WEIGHT_RAPID_TRANSACTIONS = 15
WEIGHT_AMOUNT_BALANCE_RATIO = 10


def score_high_amount(amount: float) -> float:
    """Score based on transaction amount. Higher amounts are riskier."""
    if amount > VERY_HIGH_AMOUNT_THRESHOLD:
        return WEIGHT_HIGH_AMOUNT
    if amount > HIGH_AMOUNT_THRESHOLD:
        ratio = (amount - HIGH_AMOUNT_THRESHOLD) / (
            VERY_HIGH_AMOUNT_THRESHOLD - HIGH_AMOUNT_THRESHOLD
        )
        return WEIGHT_HIGH_AMOUNT * min(ratio, 1.0) * 0.5 + WEIGHT_HIGH_AMOUNT * 0.5
    return 0.0


def score_transaction_type(tx_type: str) -> float:
    """Score based on transaction type. CASH_OUT and TRANSFER are higher risk."""
    if tx_type in HIGH_RISK_TYPES:
        return WEIGHT_TRANSACTION_TYPE
    return 0.0


def score_balance_zeroed(
    old_balance_orig: float, new_balance_orig: float, amount: float
) -> float:
    """Score when the sender's balance is zeroed out after the transaction."""
    if old_balance_orig > 0 and new_balance_orig == 0 and amount > 0:
        return WEIGHT_BALANCE_ZEROED
    return 0.0


def score_new_destination(
    dest_name: str, seen_destinations: set[str]
) -> float:
    """Score based on whether the destination account has been seen before."""
    if dest_name not in seen_destinations:
        return WEIGHT_NEW_DESTINATION
    return 0.0


def score_rapid_transactions(
    orig_name: str, transaction_counts: dict[str, int]
) -> float:
    """Score based on how many transactions the originator has made.
    More transactions in a short period indicate higher risk."""
    count = transaction_counts.get(orig_name, 0)
    if count >= 5:
        return WEIGHT_RAPID_TRANSACTIONS
    if count >= 3:
        return WEIGHT_RAPID_TRANSACTIONS * 0.6
    if count >= 2:
        return WEIGHT_RAPID_TRANSACTIONS * 0.3
    return 0.0


def score_amount_balance_ratio(amount: float, old_balance_orig: float) -> float:
    """Score when the transaction amount is disproportionate to the account balance."""
    if old_balance_orig <= 0:
        return WEIGHT_AMOUNT_BALANCE_RATIO if amount > 0 else 0.0
    ratio = amount / old_balance_orig
    if ratio > 1.0:
        return WEIGHT_AMOUNT_BALANCE_RATIO
    if ratio > 0.8:
        return WEIGHT_AMOUNT_BALANCE_RATIO * 0.6
    return 0.0


def compute_risk_score(
    transaction: dict[str, Any],
    seen_destinations: set[str],
    transaction_counts: dict[str, int],
) -> tuple[float, list[str]]:
    """Compute the overall fraud risk score for a single transaction.

    Args:
        transaction: A dictionary representing one transaction row.
        seen_destinations: Set of destination account names seen so far.
        transaction_counts: Count of transactions per originator account.

    Returns:
        A tuple of (risk_score, contributing_factors) where risk_score is
        normalized to 0-100 and contributing_factors lists the reasons.
    """
    amount = float(transaction["amount"])
    tx_type = str(transaction["type"]).strip().upper()
    old_balance_orig = float(transaction["oldbalanceOrg"])
    new_balance_orig = float(transaction["newbalanceOrig"])
    orig_name = str(transaction["nameOrig"])
    dest_name = str(transaction["nameDest"])

    total_score = 0.0
    factors: list[str] = []

    # High amount
    amt_score = score_high_amount(amount)
    if amt_score > 0:
        total_score += amt_score
        factors.append(f"High transaction amount ({amount:.2f})")

    # Transaction type
    type_score = score_transaction_type(tx_type)
    if type_score > 0:
        total_score += type_score
        factors.append(f"High-risk transaction type ({tx_type})")

    # Balance zeroed
    bal_score = score_balance_zeroed(old_balance_orig, new_balance_orig, amount)
    if bal_score > 0:
        total_score += bal_score
        factors.append("Sender balance zeroed after transaction")

    # New destination
    dest_score = score_new_destination(dest_name, seen_destinations)
    if dest_score > 0:
        total_score += dest_score
        factors.append(f"New/unseen destination account ({dest_name})")

    # Rapid transactions
    rapid_score = score_rapid_transactions(orig_name, transaction_counts)
    if rapid_score > 0:
        total_score += rapid_score
        factors.append(
            f"Rapid transactions from account ({transaction_counts.get(orig_name, 0)} txns)"
        )

    # Amount-to-balance ratio
    ratio_score = score_amount_balance_ratio(amount, old_balance_orig)
    if ratio_score > 0:
        total_score += ratio_score
        factors.append("Transaction amount disproportionate to balance")

    # Normalize to 0-100
    risk_score = min(max(round(total_score, 2), 0), 100)

    if not factors:
        factors.append("No significant risk signals detected")

    logger.debug(
        "Transaction %s scored %.2f with factors: %s",
        transaction.get("nameOrig", "unknown"),
        risk_score,
        "; ".join(factors),
    )

    return risk_score, factors
