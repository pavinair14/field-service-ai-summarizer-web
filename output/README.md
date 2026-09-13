# Verification Evidence

These files were generated from `data/service_reports.jsonl` by
`backend/run_summarizer.py`.

- `results.jsonl`: approved structured result for every input record.
- `summaries.txt`: human-readable version of the same results.
- `report_review.md`: report-by-report quality and safety review.
- `AI_OUTPUT_REVIEW.md`: intent, security, testing, performance, maintainability, and correction evidence.
- `demo.md`: short demonstration script and observed outcomes.
- `effort.md`: declared development effort and AI assistance record.

The output files are review evidence, not runtime dependencies. They can be
regenerated with the CLI at any time. No raw technician notes, contact details,
access codes, or internal validation reasons are stored in these artifacts.
