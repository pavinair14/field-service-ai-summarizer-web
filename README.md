# Field Service AI Summarizer

Customer-safe field-service summaries for the Northgate FM portal. The service
is deliberately safety-first: validation, redaction, evidence checks, and the
final publication gate remain deterministic even when optional model assistance
is configured.

## Run locally

Backend:

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Generate deterministic review artifacts without a live model:

```powershell
python run_summarizer.py ..\data\service_reports.jsonl `
	-o ..\output\results.jsonl `
	--human-output ..\output\summaries.txt
```

Frontend, in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Set `PORT_URL` and `PORT_API_KEY` only when model-assisted wording is wanted.
Without them, the deterministic customer-safe fallback is used. Credentials
must stay in a local `.env` file and must never be committed or logged.

## API contract

- `GET /health` returns a service health check.
- `GET /reports` returns selectable asset/date entries for the review UI.
- `POST /summaries` accepts `{ "report_id": "..." }` and returns the approved
	structured customer summary.
- `GET /summaries/batch` processes every non-empty JSONL record independently
	and returns one safe result per input line.

Customer summaries contain asset, visit date, findings, actions taken, parts
fitted, outstanding or recommended work, time on site, status, and a customer
caveat. Internal validation reasons, raw notes, technician IDs, and internal
report identifiers are not rendered in the customer summary UI.

Status values are `complete`, `incomplete`, `unclear`, and `unsafe`. Missing or
contradictory evidence produces a caveat instead of a guess. Visit duration is
calculated from arrival/departure timestamps; a material mismatch is marked
unclear. A whole-hour duration is displayed as `2.0 hours`, and mixed durations
as readable hours and minutes.

## Safety boundary

Technician notes are untrusted data, never instructions. The pipeline extracts
only recommendation-bearing, non-sensitive sentences from notes. It blocks
category-level patterns for names, contact details, phone numbers, email
addresses, addresses, technician identifiers, keys, access locations, and
security codes. The model receives trusted facts only, and its asset, date, and
parts claims are checked against those facts. Invalid or unsafe model output
falls back to deterministic text.

## Verification

```powershell
cd backend
pytest -q
cd ..\frontend
npm run build
npm run lint
```

Current verification: 33 backend tests pass; the batch API processes all 20
supplied reports as 16 complete, 2 incomplete, and 2 unclear results. The
known cases are FSR-3005 and FSR-3006 for contradictions, FSR-3007 and
FSR-3008 for insufficient evidence, FSR-3003 and FSR-3014 for withheld
personal/security content, FSR-3009 for instruction-like notes, and FSR-3011
for long multi-asset recommendations.

The `output/` evidence set also contains canonical structured results, readable
summaries, a report-by-report review, a demonstration, and an effort
declaration. These artifacts are generated evidence, not runtime dependencies.

## Comparison and review outcome

The attached reference projects reinforced three changes made here: stream
JSONL with record-level continuation, keep safe deterministic output when a
model is unavailable, and record evidence without copying raw notes. A real
review issue found and corrected here was an over-broad security regex that
classified ordinary text such as `alarm cleared` as access information. The
final check now requires access context such as a code, pin, location, or key.

The open conflict decision is conservative: publish reliable safe context,
mark the result `unclear`, and request follow-up rather than choosing either
contradictory value. Retrieval is intentionally out of scope because the
supplied report is the source of truth.
