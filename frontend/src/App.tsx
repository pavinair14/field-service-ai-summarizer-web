import { useEffect, useState } from "react";
import "./App.css";

type Report = {
  report_id: string;
  asset: string;
  visit_date: string;
};

type CustomerSummary = {
  asset: string;
  visit_date: string;
  findings: string;
  actions_taken: string;
  parts_fitted: string[];
  outstanding_or_recommended: string;
  time_on_site: string;
  caveat: string;
};

type SummaryResponse = {
  report_id: string;
  status: string;
  summary: CustomerSummary;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReportId, setSelectedReportId] = useState("");
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [loadingReports, setLoadingReports] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [reportsError, setReportsError] = useState("");
  const [summaryError, setSummaryError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/reports`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Unable to load reports.");
        }

        return response.json();
      })
      .then((data: Report[]) => {
        setReports(data);
      })
      .catch((err: Error) => {
        setReportsError(err.message);
      })
      .finally(() => {
        setLoadingReports(false);
      });
  }, []);

  const generateSummary = async (reportId: string) => {
    setSelectedReportId(reportId);
    setSummary(null);
    setSummaryError("");
    setLoadingSummary(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/summaries`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            report_id: reportId,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.message ||
            data.detail ||
            "Unable to generate summary."
        );
      }

      setSummary(data);
    } catch (err) {
      setSummaryError(
        err instanceof Error
          ? err.message
          : "Unable to generate summary."
      );
    } finally {
      setLoadingSummary(false);
    }
  };

  const closeSummary = () => {
    setSelectedReportId("");
    setSummary(null);
    setSummaryError("");
    setLoadingSummary(false);
  };

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && selectedReportId) closeSummary();
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [selectedReportId]);

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Operations desk / service history</p>
          <h1>Field service reports</h1>
          <p className="intro">Review technician records and generate a customer-ready summary for any visit.</p>
        </div>
        <div className="report-count" aria-label={`${reports.length} reports`}><strong>{reports.length}</strong><span>reports</span></div>
      </header>

      <section className="reports-section" aria-labelledby="reports-heading">
        <div className="section-heading">
          <div><p className="eyebrow">Service archive</p><h2 id="reports-heading">All reports</h2></div>
          <p className="section-note">Select a report to generate its summary</p>
        </div>
        {loadingReports && <p className="state-message">Loading reports...</p>}
        {reportsError && <p className="state-message error-text" role="alert">{reportsError}</p>}
        {!loadingReports && !reportsError && <div className="report-grid">
          {reports.map((report, index) => <button className="report-card" type="button" key={report.report_id} onClick={() => generateSummary(report.report_id)} style={{ "--card-delay": `${index * 35}ms` } as React.CSSProperties}>
            <span className="card-topline"><span className="report-type">Service visit</span><span className="card-arrow" aria-hidden="true">↗</span></span>
            <span className="card-asset">{report.asset}</span>
            <span className="card-meta"><span>Visit date</span><strong>{report.visit_date}</strong></span>
            <span className="card-action">View customer summary</span>
          </button>)}
        </div>}
      </section>

      {selectedReportId && <div className="modal-backdrop" role="presentation" onMouseDown={closeSummary}>
        <section className="summary-modal" role="dialog" aria-modal="true" aria-labelledby="summary-title" onMouseDown={(event) => event.stopPropagation()}>
          <button className="close-button" type="button" onClick={closeSummary} aria-label="Close summary">×</button>
          <div className="modal-header"><p className="eyebrow">Generated customer summary</p><h2 id="summary-title">{summary?.summary.asset || "Service visit"}</h2><p className="modal-subtitle">Customer-facing view</p></div>
          {loadingSummary && <div className="loading-state" role="status"><span className="spinner" aria-hidden="true" /><strong>Preparing summary</strong><span>Reviewing the trusted service details...</span></div>}
          {summaryError && <p className="modal-error" role="alert">{summaryError}</p>}
          {summary && !loadingSummary && <div className="summary-content">
            <div className="summary-facts"><div><span>Visit date</span><strong>{summary.summary.visit_date}</strong></div><div><span>Time on site</span><strong>{summary.summary.time_on_site}</strong></div><div><span>Status</span><strong className="status-value">{summary.status}</strong></div></div>
            <div className="summary-block"><h3>Findings</h3><p>{summary.summary.findings}</p></div>
            <div className="summary-block"><h3>Actions taken</h3><p>{summary.summary.actions_taken}</p></div>
            <div className="summary-block"><h3>Parts fitted</h3>{summary.summary.parts_fitted.length > 0 ? <ul className="parts-list">{summary.summary.parts_fitted.map((part) => <li key={part}>{part}</li>)}</ul> : <p>No parts recorded.</p>}</div>
            <div className="summary-block recommendation"><h3>Outstanding or recommended</h3><p>{summary.summary.outstanding_or_recommended}</p></div>
            {summary.summary.caveat && <div className="summary-block caveat"><h3>Note</h3><p>{summary.summary.caveat}</p></div>}
          </div>}
        </section>
      </div>}
    </main>
  );
}

export default App;