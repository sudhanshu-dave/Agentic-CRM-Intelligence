import { useEffect, useState } from "react";

import {
  getEmailAudit,
  getEmails,
  getThreadAudit,
  runAgentDryRun,
} from "../api/client";
import Badge from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";

const PAGE_SIZE = 10;

const filters = [
  { label: "All", params: {} },
  { label: "Critical", params: { urgency: "Critical" } },
  { label: "Needs Human", params: { requires_human: true } },
  { label: "Escalated", params: { status: "Escalated" } },
  { label: "Spam", params: { category: "Spam" } },
];

function SafeText({ children }) {
  return <span>{children || "Not available"}</span>;
}

function DecisionPanel({ agentResult }) {
  if (!agentResult) {
    return null;
  }

  const decision = agentResult.final_decision;
  const metadata = agentResult.classification_metadata || agentResult.email || {};

  if (!decision) {
    return (
      <div className="workspace-section">
        <h3>Agent Decision</h3>
        <p className="muted-text">No decision returned by the agent.</p>
      </div>
    );
  }

  return (
    <div className="workspace-section">
      <h3>Agent Decision</h3>

      <div className="decision-grid">
        <div>
          <span>Action Type</span>
          <strong>{decision.action_type}</strong>
        </div>

        <div>
          <span>Auto Reply Allowed</span>
          <strong>{decision.auto_reply_allowed ? "Yes" : "No"}</strong>
        </div>

        <div>
          <span>Requires Approval</span>
          <strong>{decision.requires_approval ? "Yes" : "No"}</strong>
        </div>

        <div>
          <span>Execute Now</span>
          <strong>{decision.execute_now ? "Yes" : "No"}</strong>
        </div>
      </div>

      <div className="workspace-section compact-section">
        <h4>LLM Classification Metadata</h4>

        <div className="decision-grid">
          <div>
            <span>Provider</span>
            <strong>{metadata.llm_provider || "fallback"}</strong>
          </div>

          <div>
            <span>Model Used</span>
            <strong>
              {metadata.model_used || "deterministic-fallback-v1"}
            </strong>
          </div>

          <div>
            <span>LLM Attempted</span>
            <strong>{metadata.llm_attempted ? "Yes" : "No"}</strong>
          </div>

          <div>
            <span>LLM Error</span>
            <strong>{metadata.llm_error || "None"}</strong>
          </div>
        </div>
      </div>

      <p className="muted-text">{decision.reason}</p>

      {agentResult.proposed_reply ? (
        <>
          <h4>Proposed Reply</h4>
          <div className="proposed-content">{agentResult.proposed_reply}</div>
        </>
      ) : (
        <p className="muted-text">
          No proposed reply generated. This is expected for unsafe cases such as
          spam or security threats.
        </p>
      )}
    </div>
  );
}

function AuditSummary({ audit }) {
  if (!audit) {
    return null;
  }

  return (
    <div className="workspace-section">
      <h3>Audit Summary</h3>

      <div className="decision-grid">
        <div>
          <span>Message ID</span>
          <strong>{audit.message_id}</strong>
        </div>

        <div>
          <span>Confidence</span>
          <strong>{audit.confidence ?? "Not classified"}</strong>
        </div>

        <div>
          <span>Priority</span>
          <strong>{audit.priority_score}</strong>
        </div>

        <div>
          <span>Actions</span>
          <strong>{audit.actions?.length || 0}</strong>
        </div>
      </div>

      {audit.actions?.length > 0 ? (
        <div className="mini-action-list">
          {audit.actions.map((action) => (
            <div className="mini-action-card" key={action.id}>
              <div className="email-meta">
                <Badge>{action.action_type}</Badge>
                <span>Action #{action.id}</span>
              </div>

              <p>
                Approved: <strong>{action.is_approved ? "Yes" : "No"}</strong>
              </p>

              {action.proposed_content ? (
                <div className="proposed-content compact">
                  {action.proposed_content}
                </div>
              ) : (
                <p className="muted-text">No proposed reply content.</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-text">No saved actions for this email yet.</p>
      )}
    </div>
  );
}

function ThreadTimeline({ threadAudit }) {
  if (!threadAudit) {
    return null;
  }

  return (
    <div className="workspace-section">
      <h3>Thread Timeline</h3>

      <div className="thread-summary-box">
        <strong>{threadAudit.thread.thread_id}</strong>
        <p>
          {threadAudit.emails.length} email(s) · Status:{" "}
          {threadAudit.thread.status}
        </p>
      </div>

      <div className="timeline">
        {threadAudit.emails.map((email) => (
          <div className="timeline-item" key={email.id}>
            <div className="timeline-dot" />

            <div className="timeline-card">
              <div className="email-card-top">
                <strong>{email.subject}</strong>
                <Badge>{email.urgency}</Badge>
              </div>

              <p>{email.timestamp}</p>
              <p>{email.body}</p>

              <div className="email-meta">
                <Badge>{email.category}</Badge>
                <Badge>{email.status}</Badge>
                <span>ID #{email.id}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function InboxPage() {
  const [activeFilter, setActiveFilter] = useState(filters[0]);
  const [page, setPage] = useState(1);

  const [emails, setEmails] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);

  const [agentResult, setAgentResult] = useState(null);
  const [audit, setAudit] = useState(null);
  const [threadAudit, setThreadAudit] = useState(null);

  const [loading, setLoading] = useState(false);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [error, setError] = useState("");

  const totalPages = pagination
    ? Math.max(1, Math.ceil(pagination.total / PAGE_SIZE))
    : 1;

  useEffect(() => {
    async function loadEmails() {
      try {
        setLoading(true);
        setError("");

        const result = await getEmails({
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE,
          ...activeFilter.params,
        });

        setEmails(result.items);
        setPagination(result.pagination);

        if (result.items.length > 0) {
          setSelectedEmail(result.items[0]);
        } else {
          setSelectedEmail(null);
        }

        setAgentResult(null);
        setAudit(null);
        setThreadAudit(null);
      } catch (err) {
        setError(
          err?.response?.data?.error?.message ||
            err.message ||
            "Could not load emails."
        );
      } finally {
        setLoading(false);
      }
    }

    loadEmails();
  }, [activeFilter, page]);

  function handleFilterChange(filter) {
    setActiveFilter(filter);
    setPage(1);
  }

  function selectEmail(email) {
    setSelectedEmail(email);
    setAgentResult(null);
    setAudit(null);
    setThreadAudit(null);
  }

  function goToPreviousPage() {
    setPage((currentPage) => Math.max(1, currentPage - 1));
  }

  function goToNextPage() {
    setPage((currentPage) => Math.min(totalPages, currentPage + 1));
  }

  async function handleRunAgent() {
    if (!selectedEmail) {
      return;
    }

    try {
      setWorkspaceLoading(true);
      setError("");

      const result = await runAgentDryRun(selectedEmail.id);
      setAgentResult(result);
    } catch (err) {
      setError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not run agent dry run."
      );
    } finally {
      setWorkspaceLoading(false);
    }
  }

  async function handleLoadAudit() {
    if (!selectedEmail) {
      return;
    }

    try {
      setWorkspaceLoading(true);
      setError("");

      const result = await getEmailAudit(selectedEmail.id);
      setAudit(result);
    } catch (err) {
      setError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not load audit."
      );
    } finally {
      setWorkspaceLoading(false);
    }
  }

  async function handleOpenThread() {
    if (!selectedEmail?.thread?.thread_id) {
      return;
    }

    try {
      setWorkspaceLoading(true);
      setError("");

      const result = await getThreadAudit(selectedEmail.thread.thread_id);
      setThreadAudit(result);
    } catch (err) {
      setError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not load thread audit."
      );
    } finally {
      setWorkspaceLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Inbox</p>
          <h1>Mission Control Inbox</h1>
          <p>
            Review emails, inspect priority, run the triage agent, and open full
            customer thread history.
          </p>
        </div>
      </div>

      {error ? <ErrorState message={error} /> : null}

      <div className="filter-bar">
        {filters.map((filter) => (
          <button
            key={filter.label}
            className={
              activeFilter.label === filter.label
                ? "filter-button filter-button-active"
                : "filter-button"
            }
            onClick={() => handleFilterChange(filter)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {loading || !pagination ? (
        <LoadingState message="Loading emails..." />
      ) : (
        <div className="inbox-workspace">
          <section className="panel inbox-list-panel">
            <div className="panel-header">
              <div>
                <h2>{activeFilter.label} Emails</h2>
                <p>
                  Showing {pagination.returned} of {pagination.total} total
                </p>
              </div>
            </div>

            <div className="email-list">
              {emails.map((email) => (
                <button
                  className={
                    selectedEmail?.id === email.id
                      ? "email-card email-card-selected"
                      : "email-card"
                  }
                  key={email.id}
                  onClick={() => selectEmail(email)}
                >
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
                </button>
              ))}
            </div>

            <div className="pagination-bar">
              <button
                className="pagination-button"
                onClick={goToPreviousPage}
                disabled={page === 1}
              >
                Previous
              </button>

              <span>
                Page <strong>{page}</strong> of <strong>{totalPages}</strong>
              </span>

              <button
                className="pagination-button"
                onClick={goToNextPage}
                disabled={page === totalPages}
              >
                Next
              </button>
            </div>
          </section>

          <section className="panel workspace-panel">
            {!selectedEmail ? (
              <p className="muted-text">Select an email to inspect it.</p>
            ) : (
              <>
                <div className="panel-header">
                  <div>
                    <h2>{selectedEmail.subject || "(No subject)"}</h2>
                    <p>{selectedEmail.sender}</p>
                  </div>

                  <div className="email-meta">
                    <Badge>{selectedEmail.category}</Badge>
                    <Badge>{selectedEmail.urgency}</Badge>
                    <Badge>{selectedEmail.status}</Badge>
                  </div>
                </div>

                <p className="email-preview">{selectedEmail.body_preview}</p>

                <div className="decision-grid">
                  <div>
                    <span>Email ID</span>
                    <strong>{selectedEmail.id}</strong>
                  </div>

                  <div>
                    <span>Priority</span>
                    <strong>{selectedEmail.priority_score}</strong>
                  </div>

                  <div>
                    <span>Requires Human</span>
                    <strong>
                      {selectedEmail.requires_human ? "Yes" : "No"}
                    </strong>
                  </div>

                  <div>
                    <span>Thread</span>
                    <strong>
                      <SafeText>{selectedEmail.thread?.thread_id}</SafeText>
                    </strong>
                  </div>
                </div>

                <div className="workspace-actions">
                  <button onClick={handleRunAgent}>Run Agent</button>
                  <button onClick={handleLoadAudit}>View Audit</button>
                  <button onClick={handleOpenThread}>Open Thread</button>
                </div>

                {workspaceLoading ? (
                  <LoadingState message="Running workspace action..." />
                ) : null}

                <DecisionPanel agentResult={agentResult} />
                <AuditSummary audit={audit} />
                <ThreadTimeline threadAudit={threadAudit} />
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}