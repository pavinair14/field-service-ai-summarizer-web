"""Generate deterministic customer-safe evidence artifacts from the supplied JSONL."""

import argparse
import json
from pathlib import Path

from app.analysis import analyze_report
from app.models import FieldServiceReport, InvalidReport
from app.output_validator import validate_customer_summary
from app.report_loader import iter_report_records
from app.safety import analyze_safety
from app.summarizer import build_deterministic_summary, build_unsafe_publication_fallback
from app.trusted_facts import build_trusted_facts


def process_record(record: FieldServiceReport | InvalidReport, line_number: int) -> dict:
    """Convert one valid or invalid input line into a safe structured evidence result."""
    if isinstance(record, InvalidReport):
        return {
            "line_number": line_number,
            "report_id": record.report_id,
            "status": "incomplete",
            "asset": record.asset,
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
        }

    analysis = analyze_report(record)
    safety = analyze_safety(record)
    facts = build_trusted_facts(record, analysis, safety)
    summary = build_deterministic_summary(facts)
    if not validate_customer_summary(summary).safe_to_publish:
        summary = build_unsafe_publication_fallback()
    return {
        "line_number": line_number,
        "report_id": record.report_id,
        "status": facts.status,
        "asset": facts.asset,
        "summary": summary.model_dump(),
    }


def render_human(result: dict) -> str:
    """Render one structured result as a readable operator evidence block."""
    summary = result["summary"]
    parts = ", ".join(summary["parts_fitted"]) or "None recorded"
    return "\n".join(
        [
            f"{result['report_id']} | {result['status']} | {summary['asset']}",
            f"Visit date: {summary['visit_date']}",
            f"Findings: {summary['findings']}",
            f"Actions taken: {summary['actions_taken']}",
            f"Parts fitted: {parts}",
            f"Outstanding or recommended: {summary['outstanding_or_recommended']}",
            f"Time on site: {summary['time_on_site']}",
            f"Caveat: {summary['caveat'] or 'None'}",
            "",
        ]
    )


def main() -> int:
    """Run the deterministic batch pipeline and write JSONL plus human-readable outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input JSONL report file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Structured JSONL output")
    parser.add_argument("--human-output", type=Path, required=True, help="Human-readable output")
    args = parser.parse_args()

    results = [
        process_record(record, line_number)
        for line_number, record in iter_report_records(args.input)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.human_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(result, ensure_ascii=True) + "\n" for result in results),
        encoding="utf-8",
    )
    args.human_output.write_text(
        "\n".join(render_human(result) for result in results),
        encoding="utf-8",
    )

    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    print(json.dumps({"count": len(results), "statuses": counts}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
