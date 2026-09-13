from pathlib import Path

from app.report_loader import load_reports

def test_load_all_services_reports():
    project_root = Path(__file__).parents[2]
    reports_path = project_root / "data" / "service_reports.jsonl"

    reports = load_reports(reports_path)

    assert len(reports) == 20
    assert reports[0].report_id == "FSR-3001"
    assert reports[-1].asset == "Pump P-03"