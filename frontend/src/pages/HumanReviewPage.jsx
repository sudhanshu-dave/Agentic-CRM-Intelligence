import { useEffect, useState } from "react";

import {
  approveAction,
  getPendingActions,
  rejectAction,
} from "../api/client";
import Badge from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";

function ActionCard({ action, onReviewed }) {
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState("");

  async function handleApprove() {
    try {
      setBusy(true);
      setLocalError("");

      await approveAction(action.id, "sudhanshu");
      await onReviewed();
    } catch (err) {
      setLocalError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not approve action."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    try {
      setBusy(true);
      setLocalError("");

      await rejectAction(
        action.id,
        "sudhanshu",
        "Rejected during human review."
      );
      await onReviewed();
    } catch (err) {
      setLocalError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not reject action."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="review-card">
      <div className="review-card-header">
        <div>
          <div className="email-meta">
            <Badge>{action.action_type}</Badge>
            <Badge>{action.review_status}</Badge>
            {action.email?.urgency ? <Badge>{action.email.urgency}</Badge> : null}
          </div>

          <h2>{action.email?.subject || "No subject"}</h2>
          <p>{action.email?.sender}</p>
        </div>

        <span className="action-id">Action #{action.id}</span>
      </div>

      <div className="decision-grid">
        <div>
          <span>Email ID</span>
          <strong>{action.email_id}</strong>
        </div>

        <div>
          <span>Category</span>
          <strong>{action.email?.category || "Unknown"}</strong>
        </div>

        <div>
          <span>Status</span>
          <strong>{action.email?.status || "Unknown"}</strong>
        </div>

        <div>
          <span>Created At</span>
          <strong>{action.created_at || "Unknown"}</strong>
        </div>
      </div>

      {action.proposed_content ? (
        <>
          <h3>Proposed Reply Draft — Approval Required</h3>
          <div className="proposed-content">{action.proposed_content}</div>
        </>
      ) : (
        <p className="muted-text">
          No proposed reply content. This is expected for blocked cases such as
          security incidents, spam, or escalation-only actions.
        </p>
      )}

      <h3>Agent Reasoning Summary</h3>

      <div className="mini-action-list">
        {(action.agent_reasoning_log || []).map((step, index) => (
          <div className="mini-action-card" key={`${step.action}-${index}`}>
            <div className="email-meta">
              <Badge>Step {index + 1}</Badge>
              <strong>{step.action}</strong>
            </div>

            <p>{step.thought}</p>
            <p className="muted-text">Next: {step.next}</p>
          </div>
        ))}
      </div>

      {localError ? <ErrorState message={localError} /> : null}

      <div className="review-actions">
        <button disabled={busy} onClick={handleApprove}>
          Approve Action
        </button>

        <button disabled={busy} className="danger-button" onClick={handleReject}>
          Reject
        </button>
      </div>
    </article>
  );
}

export default function HumanReviewPage() {
  const [actions, setActions] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadPendingActions() {
    try {
      setLoading(true);
      setError("");

      const result = await getPendingActions({ limit: 25 });
      setActions(result.items);
      setCount(result.count);
    } catch (err) {
      setError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not load pending actions."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPendingActions();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Human Review</p>
          <h1>Pending Agent Actions</h1>
          <p>
            Review AI-generated escalation plans and reply drafts before any
            action is approved.
          </p>
        </div>

        <button className="refresh-button" onClick={loadPendingActions}>
          Refresh
        </button>
      </div>

      {error ? <ErrorState message={error} /> : null}

      {loading ? (
        <LoadingState message="Loading pending actions..." />
      ) : (
        <>
          <div className="panel">
            <div className="panel-header">
              <h2>Review Queue</h2>
              <p>{count} pending action(s)</p>
            </div>
          </div>

          {actions.length === 0 ? (
            <div className="panel">
              <p className="muted-text">No pending actions right now.</p>
            </div>
          ) : (
            <div className="review-list">
              {actions.map((action) => (
                <ActionCard
                  key={action.id}
                  action={action}
                  onReviewed={loadPendingActions}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}