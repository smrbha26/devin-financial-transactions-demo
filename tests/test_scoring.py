"""Unit tests for the risk scoring module."""

import pytest

from src.scoring import (
    WEIGHT_HIGH_AMOUNT,
    WEIGHT_TRANSACTION_TYPE,
    WEIGHT_BALANCE_ZEROED,
    WEIGHT_NEW_DESTINATION,
    WEIGHT_RAPID_TRANSACTIONS,
    WEIGHT_AMOUNT_BALANCE_RATIO,
    compute_risk_score,
    score_high_amount,
    score_transaction_type,
    score_balance_zeroed,
    score_new_destination,
    score_rapid_transactions,
    score_amount_balance_ratio,
)


class TestScoreHighAmount:
    def test_below_threshold(self):
        assert score_high_amount(5000) == 0.0

    def test_at_threshold(self):
        assert score_high_amount(10_000) == 0.0

    def test_above_threshold(self):
        score = score_high_amount(50_000)
        assert score > 0
        assert score <= WEIGHT_HIGH_AMOUNT

    def test_very_high_amount(self):
        assert score_high_amount(300_000) == WEIGHT_HIGH_AMOUNT

    def test_zero_amount(self):
        assert score_high_amount(0) == 0.0


class TestScoreTransactionType:
    def test_cash_out(self):
        assert score_transaction_type("CASH_OUT") == WEIGHT_TRANSACTION_TYPE

    def test_transfer(self):
        assert score_transaction_type("TRANSFER") == WEIGHT_TRANSACTION_TYPE

    def test_payment(self):
        assert score_transaction_type("PAYMENT") == 0.0

    def test_debit(self):
        assert score_transaction_type("DEBIT") == 0.0


class TestScoreBalanceZeroed:
    def test_balance_zeroed(self):
        assert score_balance_zeroed(1000, 0, 1000) == WEIGHT_BALANCE_ZEROED

    def test_balance_not_zeroed(self):
        assert score_balance_zeroed(1000, 500, 500) == 0.0

    def test_zero_starting_balance(self):
        assert score_balance_zeroed(0, 0, 100) == 0.0

    def test_zero_amount(self):
        assert score_balance_zeroed(1000, 0, 0) == 0.0


class TestScoreNewDestination:
    def test_new_destination(self):
        assert score_new_destination("C123", set()) == WEIGHT_NEW_DESTINATION

    def test_seen_destination(self):
        assert score_new_destination("C123", {"C123", "C456"}) == 0.0


class TestScoreRapidTransactions:
    def test_no_prior_transactions(self):
        assert score_rapid_transactions("C123", {}) == 0.0

    def test_one_transaction(self):
        assert score_rapid_transactions("C123", {"C123": 1}) == 0.0

    def test_two_transactions(self):
        score = score_rapid_transactions("C123", {"C123": 2})
        assert score == WEIGHT_RAPID_TRANSACTIONS * 0.3

    def test_three_transactions(self):
        score = score_rapid_transactions("C123", {"C123": 3})
        assert score == WEIGHT_RAPID_TRANSACTIONS * 0.6

    def test_five_plus_transactions(self):
        assert score_rapid_transactions("C123", {"C123": 5}) == WEIGHT_RAPID_TRANSACTIONS


class TestScoreAmountBalanceRatio:
    def test_amount_exceeds_balance(self):
        assert score_amount_balance_ratio(1500, 1000) == WEIGHT_AMOUNT_BALANCE_RATIO

    def test_high_ratio(self):
        score = score_amount_balance_ratio(900, 1000)
        assert score == WEIGHT_AMOUNT_BALANCE_RATIO * 0.6

    def test_low_ratio(self):
        assert score_amount_balance_ratio(100, 10000) == 0.0

    def test_zero_balance_with_amount(self):
        assert score_amount_balance_ratio(500, 0) == WEIGHT_AMOUNT_BALANCE_RATIO

    def test_zero_balance_zero_amount(self):
        assert score_amount_balance_ratio(0, 0) == 0.0


class TestComputeRiskScore:
    def _make_transaction(self, **overrides):
        defaults = {
            "step": "1",
            "type": "PAYMENT",
            "amount": "100",
            "nameOrig": "C1000",
            "oldbalanceOrg": "10000",
            "newbalanceOrig": "9900",
            "nameDest": "M2000",
            "oldbalanceDest": "0",
            "newbalanceDest": "0",
        }
        defaults.update(overrides)
        return defaults

    def test_low_risk_payment(self):
        tx = self._make_transaction()
        seen = {"M2000"}
        score, factors = compute_risk_score(tx, seen, {})
        assert 0 <= score < 40
        assert isinstance(factors, list)

    def test_high_risk_cash_out(self):
        tx = self._make_transaction(
            type="CASH_OUT",
            amount="250000",
            oldbalanceOrg="250000",
            newbalanceOrig="0",
        )
        score, factors = compute_risk_score(tx, set(), {"C1000": 5})
        assert score > 70
        assert any("High-risk transaction type" in f for f in factors)
        assert any("High transaction amount" in f for f in factors)

    def test_score_capped_at_100(self):
        tx = self._make_transaction(
            type="CASH_OUT",
            amount="500000",
            oldbalanceOrg="500000",
            newbalanceOrig="0",
        )
        score, factors = compute_risk_score(tx, set(), {"C1000": 10})
        assert score <= 100

    def test_score_minimum_zero(self):
        tx = self._make_transaction(amount="0", oldbalanceOrg="0", newbalanceOrig="0")
        seen = {"M2000"}
        score, factors = compute_risk_score(tx, seen, {})
        assert score >= 0

    def test_no_factors_message(self):
        tx = self._make_transaction(
            amount="10",
            oldbalanceOrg="100000",
            newbalanceOrig="99990",
        )
        seen = {"M2000"}
        score, factors = compute_risk_score(tx, seen, {})
        assert score == 0
        assert "No significant risk signals detected" in factors
