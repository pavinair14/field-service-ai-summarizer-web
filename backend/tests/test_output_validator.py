from app.output_validator import validate_customer_summary
from app.summarizer import CustomerSummary


def make_summary(**overrides):
    data = {
        "asset": "AHU-01",
        "visit_date": "2026-01-10",
        "findings": "The filter was blocked.",
        "actions_taken": "The filter was replaced.",
        "parts_fitted": ["Filter"],
        "outstanding_or_recommended": (
            "Check the filter condition during the next visit."
        ),
        "time_on_site": "2.0 hours",
        "caveat": "",
    }

    data.update(overrides)

    return CustomerSummary(**data)


def test_clean_summary_is_safe_to_publish():
    summary = make_summary()

    result = validate_customer_summary(summary)

    assert result.safe_to_publish is True
    assert result.warnings == []


def test_iso_visit_date_is_not_treated_as_phone_number():
    summary = make_summary(visit_date="2026-03-02")

    result = validate_customer_summary(summary)

    assert result.safe_to_publish is True
    assert result.warnings == []


def test_email_is_rejected():
    summary = make_summary(
        findings="Contact john@example.com for further information."
    )

    result = validate_customer_summary(summary)

    assert result.safe_to_publish is False
    assert any("email" in warning.lower() for warning in result.warnings)


def test_phone_number_is_rejected():
    summary = make_summary(
        findings="Call 01234 567890 for further information."
    )

    result = validate_customer_summary(summary)

    assert result.safe_to_publish is False
    assert any("phone" in warning.lower() for warning in result.warnings)


def test_access_code_is_rejected():
    summary = make_summary(
        findings="The plant room access code is 123456."
    )

    result = validate_customer_summary(summary)

    assert result.safe_to_publish is False
    assert any(
        "security" in warning.lower()
        for warning in result.warnings
    )


def test_technician_id_is_rejected():
    summary = make_summary(
        findings="Technician T-123 completed the work."
    )

    result = validate_customer_summary(summary)

    assert result.safe_to_publish is False
    assert any(
        "technician" in warning.lower()
        for warning in result.warnings
    )


def test_address_is_rejected():
    summary = make_summary(findings="Visit the home address at 22 Cedar Lane.")

    result = validate_customer_summary(summary)

    assert result.safe_to_publish is False
    assert any("address" in warning.lower() for warning in result.warnings)