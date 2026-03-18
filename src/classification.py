"""
Risk classification module.

Assigns risk categories based on numeric risk scores.
"""

import logging

logger = logging.getLogger(__name__)

LOW_THRESHOLD = 40
HIGH_THRESHOLD = 70


def classify_risk(score: float) -> str:
    """Classify a risk score into a category.

    Args:
        score: Numeric risk score between 0 and 100.

    Returns:
        Risk category string: "LOW", "MEDIUM", or "HIGH".

    Raises:
        ValueError: If score is outside the 0-100 range.
    """
    if score < 0 or score > 100:
        raise ValueError(f"Risk score must be between 0 and 100, got {score}")

    if score < LOW_THRESHOLD:
        category = "LOW"
    elif score <= HIGH_THRESHOLD:
        category = "MEDIUM"
    else:
        category = "HIGH"

    logger.debug("Score %.2f classified as %s", score, category)
    return category
