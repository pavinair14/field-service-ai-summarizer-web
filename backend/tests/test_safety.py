from datetime import datetime

from app.models import FieldServiceReport
from app.safety import analyze_safety


def make_report(**overrides):
    data = {
        "report_id": "FSR-123",
        "asset": "Asset 1",
        "technician_id": "T-123456",
        "arrived_at": datetime(2023, 1, 1, 8, 0),
        "departed_at": datetime(2023, 1, 1, 10, 0),
        "stated_duration_hours": 2.0,
        "parts_used": [],
        "resolution": "Resolution 1",
        "technician_notes": "Technician notes 1",
        
    }
    data.update(overrides)
    return FieldServiceReport(**data)

def test_email_is_detected():
    report = make_report(technician_notes="Contact me at john.doe@example.com")

    result = analyze_safety(report)

    assert result.contains_personal_information is True

def test_phone_number_is_detected():
    report = make_report(technician_notes="Call me at +1 (555) 123-4567")

    result = analyze_safety(report)

    assert result.contains_personal_information is True


def test_personal_address_is_detected():
    report = make_report(technician_notes="Home address: 22 Cedar Lane.")

    result = analyze_safety(report)

    assert result.contains_personal_information is True

def test_access_code_is_detected():
    report = make_report(technician_notes="The access code is 1234")

    result = analyze_safety(report)

    assert result.contains_physical_security_information is True

def test_clean_report_has_no_personal_or_security_info():
    report = make_report(technician_id="")

    result = analyze_safety(report)

    assert result.contains_personal_information is False
    assert result.contains_physical_security_information is False
    assert result.contains_technical_information is False

from pathlib import Path

from app.report_loader import load_reports

def load_test_reports():
   project_root = Path(__file__).resolve().parents[2]
   reports_path = project_root / "data" / "service_reports.jsonl"
   return load_reports(reports_path)

def test_sensitive_information_detection_in_real_reports():
    reports = load_test_reports()

    analyses = {
        report.report_id: analyze_safety(report)
        for report in reports
    }

    assert analyses["FSR-3003"].contains_personal_information is True
    assert analyses["FSR-3003"].contains_physical_security_information is True
    assert analyses["FSR-3003"].contains_technical_information is True