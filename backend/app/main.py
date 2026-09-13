from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
from pydantic import BaseModel

from .analysis import analyze_report
from .output_validator import validate_customer_summary
from .models import FieldServiceReport, InvalidReport
from .report_loader import iter_report_records, load_reports
from .safety import analyze_safety
from .summarizer import (
    build_deterministic_summary,
    build_unsafe_publication_fallback,
    generate_customer_summary_result,
    summarize_with_llm,
)
from .trusted_facts import build_trusted_facts

app = FastAPI(
    title="Field Service Reporting API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "service_reports.jsonl"
)

class SummaryRequest(BaseModel):
    report_id: str


def _customer_result(report: FieldServiceReport) -> dict:
    """Build one approved result while keeping model wording behind deterministic gates.

    Delegates to generate_customer_summary_result which runs validate_customer_summary
    and checks safe_to_publish before returning the final summary.
    """
    return generate_customer_summary_result(report)


@app.get("/health")
def health_check():
    """Return a lightweight liveness response for the service process."""
    return {"status": "ok"}

@app.get("/reports")
def list_reports():
    """Return safe asset/date choices for the review interface."""
    reports = load_reports(DATA_FILE)

    return [
        {
            "report_id": report.report_id,
            "asset": report.asset,
            "visit_date": report.arrived_at.date().isoformat()
        }
        for report in reports
    ]


@app.post("/summaries")
def create_summary(request: SummaryRequest):
    """Generate one customer-safe summary for the requested report."""
    reports = load_reports(DATA_FILE)

    report = next(
        (
            report
            for report in reports
            if report.report_id == request.report_id
        ),
        None,
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Report not found: {request.report_id}"
        )

    result = _customer_result(report)
    return {"report_id": report.report_id, **result}


@app.get("/summaries/batch")
def create_batch_summary():
    """Process every JSONL record independently so malformed input cannot stop the batch."""
    results = []
    for line_number, record in iter_report_records(DATA_FILE):
        if isinstance(record, InvalidReport):
            results.append({
                "status": "incomplete",
                "summary": {
                    "asset": record.asset,
                    "visit_date": "Unknown",
                    "findings": "The report could not be validated.",
                    "actions_taken": "No customer-facing action can be confirmed.",
                    "parts_fitted": [],
                    "outstanding_or_recommended": "This report requires follow-up.",
                    "time_on_site": "Unclear",
                    "caveat": "This report is incomplete and requires follow-up.",
                },
                "line_number": line_number,
            })
        else:
            results.append({"line_number": line_number, **_customer_result(record)})
    return {"count": len(results), "results": results}
   
    