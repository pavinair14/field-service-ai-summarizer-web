# Demonstration

## 1. Start the backend

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

## 2. Review a normal report

Open the frontend and select the Chiller CH-04 visit. The customer view shows
the visit date, filter-drier action, fitted part, and calculated 2 hours 30
minutes on site. No technician ID or raw note is displayed.

## 3. Review a safety-sensitive report

Select the Boiler BLR-02 visit. The safe ignition-electrode outcome remains
available, while personal and physical-security details from the internal note
do not appear in the customer view.

## 4. Review uncertainty

Select Chiller CH-01 or Cooling tower CT-02. The result is `unclear` and asks
for follow-up rather than silently choosing between conflicting duration or
parts evidence.

## 5. Verify batch behavior

```powershell
cd backend
python run_summarizer.py ..\data\service_reports.jsonl `
  -o ..\output\results.jsonl `
  --human-output ..\output\summaries.txt
```

Observed result: 20 records processed, 16 complete, 2 incomplete, and 2
unclear. A model is not required for the demonstration.
