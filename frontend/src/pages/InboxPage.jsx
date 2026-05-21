import { useEffect, useState } from "react";

import { getEmails } from "../api/client";
import Badge from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";

const filters = [
  { label: "All", params: {} },
  { label: "Critical", params: { urgency: "Critical" } },
  { label: "Needs Human", params: { requires_human: true } },
  { label: "Escalated", params: { status: "Escalated" } },
  { label: "Spam", params: { category: "Spam" } },
];

export default function InboxPage() {
  const [activeFilter, setActiveFilter] = useState(filters[0]);
  const [emails, setEmails] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadEmails() {
      try {
        setError("");
        const result = await getEmails({
          limit: 25,
          ...activeFilter.params,
        });
        setEmails(result.items);
        setPagination(result.pagination);
      } catch (err) {
        setError(
          err?.response?.data?.error?.message ||
            err.message ||
            "Could not load emails."
        );
      }
    }

    loadEmails();
  }, [activeFilter]);

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Inbox</p>
          <h1>Mission Control Inbox</h1>
          <p>Filter emails by urgency, status, and human-review need.</p>
        </div>
      </div>

      <div className="filter-bar">
        {filters.map((filter) => (
          <button
            key={filter.label}
            className={
              activeFilter.label === filter.label
                ? "filter-button filter-button-active"
                : "filter-button"
            }
            onClick={() => setActiveFilter(filter)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {!pagination ? (
        <LoadingState message="Loading emails..." />
      ) : (
        <div className="panel">
          <div className="panel-header">
            <h2>{activeFilter.label} Emails</h2>
            <p>{pagination.total} total</p>
          </div>

          <div className="email-list">
            {emails.map((email) => (
              <article className="email-card" key={email.id}>
                <div className="email-card-top">
                  <div>
                    <strong>{email.subject || "(No subject)"}</strong>
                    <p>{email.sender}</p>
                  </div>

                  <Badge>{email.urgency}</Badge>
                </div>

                <p className="email-preview">{email.body_preview}</p>

                <div className="email-meta">
                  <Badge>{email.category}</Badge>
                  <Badge>{email.status}</Badge>
                  {email.requires_human ? <Badge>Needs Human</Badge> : null}
                  <span>ID #{email.id}</span>
                  <span>Priority {email.priority_score}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}