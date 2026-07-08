"""Pytest test suite for the PII detection engine and risk scoring.

Tests each regex pattern independently, verifies the Luhn algorithm
for credit card detection, checks for false positives, and validates
risk calculation at each severity tier.
"""

import pytest

from app.services.detection.detection_engine import (
    DetectionEngine,
    _luhn_check,
    _filter_credit_cards,
)


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def engine() -> DetectionEngine:
    """Provide a fresh DetectionEngine instance per test."""
    return DetectionEngine()


# ======================================================================
# Luhn algorithm unit tests
# ======================================================================


class TestLuhnCheck:
    """Verify the Luhn algorithm implementation."""

    def test_valid_visa(self) -> None:
        assert _luhn_check("4111111111111111") is True

    def test_valid_mastercard(self) -> None:
        assert _luhn_check("5500000000000004") is True

    def test_valid_amex(self) -> None:
        assert _luhn_check("378282246310005") is True

    def test_invalid_number(self) -> None:
        assert _luhn_check("1234567890123456") is False

    def test_too_short(self) -> None:
        assert _luhn_check("123") is False

    def test_too_long(self) -> None:
        assert _luhn_check("12345678901234567890") is False

    def test_empty_string(self) -> None:
        assert _luhn_check("") is False

    def test_with_spaces(self) -> None:
        """Luhn check strips non-digit characters."""
        assert _luhn_check("4111 1111 1111 1111") is True

    def test_with_dashes(self) -> None:
        assert _luhn_check("4111-1111-1111-1111") is True


# ======================================================================
# Credit card filtering
# ======================================================================


class TestFilterCreditCards:
    """Verify that _filter_credit_cards rejects non-Luhn matches."""

    def test_all_valid(self) -> None:
        candidates = ["4111111111111111", "5500000000000004"]
        assert _filter_credit_cards(candidates) == candidates

    def test_all_invalid(self) -> None:
        assert _filter_credit_cards(["1234567890123456"]) == []

    def test_mixed(self) -> None:
        result = _filter_credit_cards(
            ["4111111111111111", "1234567890123456", "5500000000000004"]
        )
        assert result == ["4111111111111111", "5500000000000004"]


# ======================================================================
# Aadhaar detection
# ======================================================================


class TestDetectAadhaar:
    """Aadhaar: 12 digits, first digit 2-9."""

    def test_detect_single(self, engine: DetectionEngine) -> None:
        text = "My Aadhaar is 234512345678"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Aadhaar"]["count"] == 1
        assert results["Aadhaar"]["severity"] == "CRITICAL"
        assert "234512345678" in results["Aadhaar"]["sample_values"]

    def test_detect_multiple(self, engine: DetectionEngine) -> None:
        text = "Aadhaar1: 234512345678, Aadhaar2: 345678901234"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Aadhaar"]["count"] == 2

    def test_reject_starting_with_0_or_1(self, engine: DetectionEngine) -> None:
        """Aadhaar numbers should not start with 0 or 1."""
        text = "Invalid: 012345678912 and 123456789012"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Aadhaar" not in results

    def test_reject_short_number(self, engine: DetectionEngine) -> None:
        text = "Too short: 2345678901"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Aadhaar" not in results

    def test_reject_long_number(self, engine: DetectionEngine) -> None:
        text = "Too long: 23451234567899"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Aadhaar" not in results


# ======================================================================
# PAN detection
# ======================================================================


class TestDetectPAN:
    """PAN: 5 uppercase letters, 4 digits, 1 uppercase letter."""

    def test_detect_single(self, engine: DetectionEngine) -> None:
        text = "PAN: ABCDE1234F"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["PAN"]["count"] == 1
        assert results["PAN"]["severity"] == "HIGH"
        assert "ABCDE1234F" in results["PAN"]["sample_values"]

    def test_detect_multiple(self, engine: DetectionEngine) -> None:
        text = "PAN1: ABCDE1234F, PAN2: XYZAB5678G"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["PAN"]["count"] == 2

    def test_reject_lowercase(self, engine: DetectionEngine) -> None:
        text = "Lowercase: abcde1234f"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "PAN" not in results

    def test_reject_wrong_length(self, engine: DetectionEngine) -> None:
        text = "Too short: ABCDE123, too long: ABCDE12345"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "PAN" not in results

    def test_reject_invalid_pattern(self, engine: DetectionEngine) -> None:
        text = "Not PAN: 12345ABCDE"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "PAN" not in results


# ======================================================================
# Email detection
# ======================================================================


class TestDetectEmail:
    """Email: standard RFC-like pattern."""

    def test_detect_simple(self, engine: DetectionEngine) -> None:
        text = "Email: user@example.com"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Email"]["count"] == 1
        assert results["Email"]["severity"] == "LOW"
        assert "user@example.com" in results["Email"]["sample_values"]

    def test_detect_multiple(self, engine: DetectionEngine) -> None:
        text = "a@b.com, c@d.co.in"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Email"]["count"] == 2

    def test_with_special_chars(self, engine: DetectionEngine) -> None:
        """Emails with dots, plus signs, and underscores are valid."""
        text = "Contact: first.last+tag@sub.example.co.uk"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Email"]["count"] == 1
        assert "first.last+tag@sub.example.co.uk" in results["Email"]["sample_values"]

    def test_reject_no_domain(self, engine: DetectionEngine) -> None:
        text = "Not email: user@"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Email" not in results


# ======================================================================
# Phone (India) detection
# ======================================================================


class TestDetectPhone:
    """Indian phone: optional +91/0 prefix, starts with 6-9, 10 digits."""

    def test_detect_10_digit(self, engine: DetectionEngine) -> None:
        text = "Phone: 9876543210"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Phone"]["count"] == 1
        assert results["Phone"]["severity"] == "MEDIUM"
        assert "9876543210" in results["Phone"]["sample_values"]

    def test_detect_with_plus91(self, engine: DetectionEngine) -> None:
        text = "Phone: +919876543210"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Phone"]["count"] == 1
        assert "+919876543210" in results["Phone"]["sample_values"]

    def test_detect_with_zero_prefix(self, engine: DetectionEngine) -> None:
        text = "Phone: 09876543210"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Phone"]["count"] == 1
        assert "09876543210" in results["Phone"]["sample_values"]

    def test_detect_multiple(self, engine: DetectionEngine) -> None:
        text = "Phones: 9876543210, +918765432109, 07654321098"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["Phone"]["count"] == 3

    def test_reject_starts_with_5(self, engine: DetectionEngine) -> None:
        text = "Invalid: 5123456789"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Phone" not in results

    def test_reject_too_short(self, engine: DetectionEngine) -> None:
        text = "Too short: 987654321"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Phone" not in results


# ======================================================================
# Credit card detection
# ======================================================================


class TestDetectCreditCard:
    """Credit card: 13-16 digits, validated with Luhn."""

    def test_detect_visa(self, engine: DetectionEngine) -> None:
        text = "CC: 4111111111111111"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["CreditCard"]["count"] == 1
        assert results["CreditCard"]["severity"] == "CRITICAL"
        assert "4111111111111111" in results["CreditCard"]["sample_values"]

    def test_detect_mastercard(self, engine: DetectionEngine) -> None:
        text = "CC: 5500000000000004"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["CreditCard"]["count"] == 1

    def test_detect_amex(self, engine: DetectionEngine) -> None:
        text = "CC: 378282246310005"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["CreditCard"]["count"] == 1

    def test_detect_with_spaces(self, engine: DetectionEngine) -> None:
        text = "CC: 4111 1111 1111 1111"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["CreditCard"]["count"] == 1
        # The raw match includes spaces; ensure Luhn strips them
        assert len(results["CreditCard"]["sample_values"]) == 1

    def test_detect_with_dashes(self, engine: DetectionEngine) -> None:
        text = "CC: 4111-1111-1111-1111"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert results["CreditCard"]["count"] == 1

    def test_reject_invalid_luhn(self, engine: DetectionEngine) -> None:
        """Valid card format but fails Luhn must be rejected."""
        text = "CC: 1234567890123456"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "CreditCard" not in results


# ======================================================================
# False positive tests
# ======================================================================


class TestNoFalsePositives:
    """Ensure common non-PII text is not flagged."""

    def test_plain_text(self, engine: DetectionEngine) -> None:
        text = (
            "This is a simple document with no sensitive information. "
            "The quick brown fox jumps over the lazy dog. "
            "Contact us at our website for more details."
        )
        results = engine.detect(text)
        assert len(results) == 0

    def test_only_numbers(self, engine: DetectionEngine) -> None:
        text = "Values: 100, 200, 300, 400. Total: 1000"
        results = engine.detect(text)
        assert len(results) == 0

    def test_dates_only(self, engine: DetectionEngine) -> None:
        text = "Dates: 2024-01-15, 2023-12-25, 1990-05-20"
        results = engine.detect(text)
        # 1990-05-20 could match a 10-digit sequence depending on separation
        # but without separators the regex should not trigger for PAN/Aadhaar
        assert len(results) == 0

    def test_ip_addresses(self, engine: DetectionEngine) -> None:
        text = "IPs: 192.168.1.1, 10.0.0.1, 172.16.0.1"
        results = engine.detect(text)
        assert len(results) == 0

    def test_pan_like_but_invalid(self, engine: DetectionEngine) -> None:
        """Sequences that look like PAN but are not valid."""
        text = "AAAAA1111B"  # All same letter is an unusual PAN prefix
        results = {r["data_type"]: r for r in engine.detect(text)}
        # This technically matches the PAN regex, but is an edge case.
        # Our engine matches the regex; real-world validation would
        # typically cross-reference a PAN database.
        assert "PAN" in results

    def test_phone_like_in_context(self, engine: DetectionEngine) -> None:
        """A number that looks like a phone but starts with 5 should not match."""
        text = "Reference: 5123456789 is an invalid phone start"
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Phone" not in results

    def test_aadhaar_in_consecutive_digits(self, engine: DetectionEngine) -> None:
        """Only 12-digit numbers starting with 2-9 should match Aadhaar."""
        text = "Some number: 999999999999"  # 12 digits, starts with 9
        results = {r["data_type"]: r for r in engine.detect(text)}
        assert "Aadhaar" in results


# ======================================================================
# Risk calculation tests
# ======================================================================

# We test risk calculation logic directly from the detection engine
# output. The full RiskService is tested separately, but we verify
# the weighting math here using the same constants as in risk_service.


def _calculate_risk_score(findings: list[dict]) -> float:
    """Replicate risk score calculation to test independently."""
    weights = {
        "Aadhaar": 50.0,
        "PAN": 40.0,
        "CreditCard": 60.0,
        "Email": 10.0,
        "Phone": 10.0,
    }
    score = 0.0
    for finding in findings:
        weight = weights.get(finding["data_type"], 20.0)
        score += finding["count"] * weight
    return score


def _risk_level(score: float) -> str:
    if score <= 30.0:
        return "LOW"
    elif score <= 70.0:
        return "MEDIUM"
    else:
        return "HIGH"


class TestRiskCalculation:
    """Verify risk scoring calculations using detection engine output."""

    def test_risk_calculation_low(self, engine: DetectionEngine) -> None:
        """Only low-weight findings should yield LOW risk."""
        text = "Emails: user@example.com, admin@test.com"
        results = engine.detect(text)
        score = _calculate_risk_score(results)
        assert score <= 30.0
        assert _risk_level(score) == "LOW"

    def test_risk_calculation_medium(self, engine: DetectionEngine) -> None:
        """A phone number alone should push score into MEDIUM range."""
        text = "Phone: +919876543210"
        results = engine.detect(text)
        score = _calculate_risk_score(results)
        assert _risk_level(score) == "MEDIUM"

    def test_risk_calculation_high(self, engine: DetectionEngine) -> None:
        """Multiple high-weight findings should yield HIGH risk."""
        text = (
            "Aadhaar: 234512345678, "
            "PAN: ABCDE1234F, "
            "CreditCard: 4111111111111111"
        )
        results = engine.detect(text)
        score = _calculate_risk_score(results)
        assert score > 70.0
        assert _risk_level(score) == "HIGH"

    def test_risk_score_exact_values(self, engine: DetectionEngine) -> None:
        """Verify exact score for a known mix of findings."""
        text = (
            "Email: user@example.com, "
            "Phone: 9876543210"
        )
        results = engine.detect(text)
        score = _calculate_risk_score(results)
        # Email (10 * 1) + Phone (10 * 1) = 20
        assert score == 20.0
        assert _risk_level(score) == "LOW"

    def test_high_risk_with_credit_card_only(self, engine: DetectionEngine) -> None:
        """A single credit card (weight 60) does not exceed 71 alone."""
        text = "CC: 4111111111111111"
        results = engine.detect(text)
        score = _calculate_risk_score(results)
        # CreditCard weight = 60, so 1 * 60 = 60
        assert score == 60.0
        assert _risk_level(score) == "MEDIUM"

    def test_empty_no_findings(self, engine: DetectionEngine) -> None:
        text = "No sensitive data here."
        results = engine.detect(text)
        score = _calculate_risk_score(results)
        assert score == 0.0
        assert _risk_level(score) == "LOW"
