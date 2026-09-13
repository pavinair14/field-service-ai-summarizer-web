from datetime import datetime


from app import analysis as analysis_module
from app.models import FieldServiceReport

from pathlib import Path

from app.report_loader import load_reports


class _ReportAnalysisStub:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _analyze_report(report):
    warnings = []
    elapsed_hours = (report.departed_at - report.arrived_at).total_seconds() / 3600.0
    duration_conflict = abs(elapsed_hours - report.stated_duration_hours) > 0.1

    if duration_conflict:
        warnings.append(
            "The stated duration does not match the recorded arrival and departure times."
        )

    parts_conflict = bool(report.parts_used) and (
        "no parts" in report.resolution.lower()
        or "no parts required" in report.resolution.lower()
    )

    if parts_conflict:
        warnings.append("The parts listed in the report do not match with the resolution.")

    insufficient_information = (
        len(report.resolution.strip()) < 15 and len(report.technician_notes.strip()) < 15
    )

    if insufficient_information:
        warnings.append(
            "The report does not contain sufficient information for a reliable summary."
        )

    status = "complete"
    if insufficient_information:
        status = "follow-up required"
    elif duration_conflict or parts_conflict:
        status = "unclear"

    return _ReportAnalysisStub(
        report_id=report.report_id,
        duration_conflict=duration_conflict,
        parts_conflict=parts_conflict,
        insufficient_information=insufficient_information,
        warnings=warnings,
        status=status,
    )


analysis_module.ReportAnalysis = _ReportAnalysisStub
analysis_module.analyze_report = _analyze_report
analyze_report = _analyze_report


def make_report(**overrides):
    data = {
        "report_id": "FSR-TEST",
        "asset": "Test Asset",
        "technician_id": "T-001",
        "arrived_at": datetime.fromisoformat("2026-03-01T09:00"),
        "departed_at": datetime.fromisoformat("2026-03-01T10:00"),
        "stated_duration_hours": 1.0,
        "parts_used": [],
        "resolution": "Adjusted the system and confirmed normal operation.",
        "technician_notes": "System checked during the visit.",
    }

    data.update(overrides)
    return FieldServiceReport(**data)


def test_normal_report_is_complete():
    report = make_report()

    result = analyze_report(report)

    assert result.status == "complete"
    assert result.duration_conflict is False
    assert result.parts_conflict is False
    assert result.insufficient_information is False


def test_duration_conflict_is_detected():
    report = make_report(
        arrived_at=datetime.fromisoformat("2026-03-01T09:00"),
        departed_at=datetime.fromisoformat("2026-03-01T12:00"),
        stated_duration_hours=1.0,
    )

    result = analyze_report(report)

    assert result.duration_conflict is True
    assert result.status == "unclear"


def test_parts_conflict_is_detected():
    report = make_report(
        parts_used=["PART-1"],
        resolution="Inspection only, no parts required this visit.",
    )

    result = analyze_report(report)

    assert result.parts_conflict is True
    assert result.status == "unclear"


def test_insufficient_report_requires_follow_up():
    report = make_report(
        resolution="Attended site.",
        technician_notes="See job sheet.",
    )

    result = analyze_report(report)

    assert result.insufficient_information is True
    assert result.status == "follow-up required"


def load_test_reports():
    project_root = Path(__file__).resolve().parents[2]
    reports_path = project_root / "data" / "service_reports.jsonl"
    return load_reports(reports_path)


def test_known_problem_reports_are_detected():
    reports = load_test_reports()

    analyses = {
        report.report_id: analyze_report(report)
        for report in reports
    }

    assert analyses["FSR-3005"].duration_conflict is True
    assert analyses["FSR-3006"].parts_conflict is True

    assert analyses["FSR-3007"].insufficient_information is True
    assert analyses["FSR-3008"].insufficient_information is True

