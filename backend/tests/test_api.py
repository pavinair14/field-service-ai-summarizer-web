from fastapi.testclient import TestClient

from app.main import app

from unittest.mock import patch

from app.summarizer import CustomerSummary


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_reports_returns_all_reports():
    response = client.get("/reports")

    assert response.status_code == 200

    reports = response.json()

    assert len(reports) == 20
    assert reports[0]["report_id"]


def test_missing_report_returns_404():
    response = client.post(
        "/summaries",
        json={"report_id": "DOES-NOT-EXIST"},
    )

    assert response.status_code == 404

def test_summary_endpoint_has_publication_safety_boundary():
    source = open(
        "app/main.py",
        encoding="utf-8",
    ).read()

    assert "validate_customer_summary" in source
    assert "safe_to_publish" in source

def test_summary_endpoint_returns_generated_summary():
    fake_summary = CustomerSummary(
        asset="Chiller CH-04",
        visit_date="2026-03-02",
        findings="The filter-drier was blocked.",
        actions_taken="The filter-drier was replaced.",
        parts_fitted=["filter-drier FD-22"],
        outstanding_or_recommended=(
            "Check the filter condition during the next visit."
        ),
        time_on_site="2.0 hours",
        caveat="",
    )

    with patch(
        "app.main.summarize_with_llm",
        return_value=fake_summary,
    ):
        response = client.post(
            "/summaries",
            json={"report_id": "FSR-3001"},
        )

    assert response.status_code == 200

    body = response.json()

    assert body["report_id"] == "FSR-3001"
    assert body["summary"]["asset"] == "Chiller CH-04"
    assert body["summary"]["parts_fitted"] == ["filter-drier FD-22"]

def test_summary_endpoint_blocks_unsafe_generated_output():
    unsafe_summary = CustomerSummary(
        asset="AHU-01",
        visit_date="2026-01-10",
        findings="Contact john@example.com for more information.",
        actions_taken="Inspection completed.",
        parts_fitted=[],
        outstanding_or_recommended="No further action recorded.",
        time_on_site="2.0 hours",
        caveat="",
    )

    with patch(
        "app.main.summarize_with_llm",
        return_value=unsafe_summary,
    ):
        response = client.post(
            "/summaries",
            json={"report_id": "FSR-3001"},
        )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "complete"
    assert "john@example.com" not in str(body)


