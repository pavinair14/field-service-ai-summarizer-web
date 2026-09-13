from app.models import FieldServiceReport

def test_field_service_report_model():
    report_data = {
        "report_id": "FSR-TEST",
        "asset": "Test Asset",
        "technician_id": "T-001",
        "arrived_at": "2023-03-01T08:00:00Z",
        "departed_at": "2023-03-01T10:00:00Z",
        "stated_duration_hours": 2.0,
        "parts_used": ["Part A", "Part B"],
        "resolution": "Test resolution",
        "technician_notes": "Test notes",
    }

    report = FieldServiceReport.model_validate(report_data)

    assert report.report_id == report_data["report_id"]
    assert report.asset == report_data["asset"]
    assert report.parts_used == report_data["parts_used"]