from datetime import datetime

from app.analysis import analyze_report
from app.models import FieldServiceReport
from app.safety import analyze_safety
from app.trusted_facts import build_trusted_facts


def make_report(**overrides):
    data = {
        "report_id": "TEST-001",
        "asset": "AHU-01",
        "technician_id": "T-001",
        "arrived_at": datetime(2026, 1, 10, 9, 0),
        "departed_at": datetime(2026, 1, 10, 11, 0),
        "stated_duration_hours": 2.0,
        "parts_used": ["Filter"],
        "resolution": "Replaced blocked filter and restored normal operation.",
        "technician_notes": "Recommend checking filter condition during the next visit.",
    }

    data.update(overrides)
    return FieldServiceReport(**data)


def test_build_trusted_facts_contains_customer_relevant_information():
    report = make_report()

    analysis = analyze_report(report)
    safety = analyze_safety(report)

    facts = build_trusted_facts(report, analysis, safety)

    assert facts.report_id == "TEST-001"
    assert facts.asset == "AHU-01"
    assert facts.visit_date == "2026-01-10"
    assert "filter" in facts.findings.lower()
    assert facts.parts_fitted == ["Filter"]
    assert facts.time_on_site == "2.0 hours"


def test_conflicting_duration_is_not_silently_resolved():
    report = make_report(
        stated_duration_hours=4.0,
    )

    analysis = analyze_report(report)
    safety = analyze_safety(report)

    facts = build_trusted_facts(report, analysis, safety)

    assert facts.status == "unclear"
    assert "Unclear" in facts.time_on_site
    assert any("duration" in caveat.lower() for caveat in facts.caveats)


def test_sensitive_information_is_not_copied_into_customer_facts():
    report = make_report(
        technician_notes=(
            "Contact engineer at john@example.com. "
            "Plant room access code is 123456."
        )
    )

    analysis = analyze_report(report)
    safety = analyze_safety(report)

    facts = build_trusted_facts(report, analysis, safety)

    assert "john@example.com" not in facts.caveats
    assert "123456" not in facts.caveats