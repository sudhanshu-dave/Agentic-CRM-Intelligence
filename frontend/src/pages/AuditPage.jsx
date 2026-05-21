import { useState } from "react";

import { getEmailAudit, runAgentDryRun } from "../api/client";
import Badge from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";

function formatValue(value) {
  if (value === null || value === undefined) {
    return "None";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "None";
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function ObservationBlock({ observation }) {
  if (!observation || typeof observation !== "object") {
    return <p>{formatValue(observation)}</p>;
  }

  return (
    <div className="observation-grid">
      {Object.entries(observation).map(([key, value]) => (
        <div className="observation-row" key={key}>
          <span>{key.replaceAll("_", " ")}</span>
          <strong>{formatValue(value)}</strong>
        </div>
      ))}
    </div>
  );
}

function ReasoningTrace({ trace }) {
  if (!trace || trace.length === 0) {
    return <p className="muted-text">No reasoning trace available.</p>;
  }

  return (
    <div className="trace-list">
      {trace.map((step, index) => (
        <div className="trace-card" key={`${step.action}-${index}`}>
          <div className="trace-step-header">
            <Badge>Step {index + 1}</Badge>
            <strong>{step.action}</strong>
          </div>

          <div className="trace-section">
            <span>Thought</span>
            <p>{step.thought}</p>
          </div>

          <div className="trace-section">
            <span>Observation</span>
            <ObservationBlock observation={step.observation} />
          </div>

          <div className="trace-section">
            <span>Next</span>
            <p>{step.next}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function ActionCard({ action }) {
  return (
    <div className="trace-card">
      <div className="trace-step-header">
        <Badge>{action.action_type}</Badge>
        <span>Action #{action.id}</span>
      </div>

      <div className="decision-grid">
        <div>
          <span>Approved</span>
          <strong>{action.is_approved ? "Yes" : "No"}</strong>
        </div>

        <div>
          <span>Approved By</span>
          <strong>{action.approved_by || "Not approved yet"}</strong>
        </div>

        <div>
          <span>Executed At</span>
          <strong>{action.executed_at || "Not executed"}</strong>
        </div>

        <div>
          <span>Created At</span>
          <strong>{action.created_at || "Unknown"}</strong>
        </div>
      </div>

      {action.proposed_content ? (
        <>
          <h4>Proposed Content</h4>
          <div className="proposed-content">{action.proposed_content}</div>
        </>
      ) : (
        <p className="muted-text">No proposed reply content. This is expected for unsafe cases like security threats or spam.</p>
      )}

      <h4>Reasoning Trace</h4>
      <ReasoningTrace trace={action.agent_reasoning_log} />
    </div>
  );
}

export default function AuditPage() {
  const [emailId, setEmailId] = useState("60");
  const [audit, setAudit] = useState(null);
  const [agentResult, setAgentResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadAudit() {
    try {
      setLoading(true);
      setError("");
      setAgentResult(null);

      const result = await getEmailAudit(emailId);
      setAudit(result);
    } catch (err) {
      setError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not load audit."
      );
    } finally {
      setLoading(false);
    }
  }

  async function runAgent() {
    try {
      setLoading(true);
      setError("");

      const result = await runAgentDryRun(emailId);
      setAgentResult(result);
    } catch (err) {
      setError(
        err?.response?.data?.error?.message ||
          err.message ||
          "Could not run agent."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Audit</p>
          <h1>Agent Reasoning and Audit Trail</h1>
          <p>Inspect classification, heuristic flags, saved actions, and agent reasoning steps.</p>
        </div>
      </div>

      <div className="control-row">
        <input
          value={emailId}
          onChange={(event) => setEmailId(event.target.value)}
          placeholder="Email ID e.g. 60"
        />

        <button onClick={loadAudit}>Load Audit</button>
        <button onClick={runAgent}>Run Agent Dry Run</button>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {loading ? <LoadingState message="Loading audit data..." /> : null}

      {audit ? (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2>{audit.subject}</h2>
              <p>{audit.sender}</p>
            </div>

            <div className="email-meta">
              <Badge>{audit.category}</Badge>
              <Badge>{audit.urgency}</Badge>
              <Badge>{audit.status}</Badge>
            </div>
          </div>

          <p className="email-preview">{audit.body}</p>

          <div className="decision-grid">
            <div>
              <span>Message ID</span>
              <strong>{audit.message_id}</strong>
            </div>

            <div>
              <span>Priority Score</span>
              <strong>{audit.priority_score}</strong>
            </div>

            <div>
              <span>Confidence</span>
              <strong>{audit.confidence ?? "Not classified"}</strong>
            </div>

            <div>
              <span>Requires Human</span>
              <strong>{audit.requires_human ? "Yes" : "No"}</strong>
            </div>
          </div>

          <h3>Heuristic Flags</h3>

          <div className="flag-grid">
            {Object.entries(audit.heuristic_flags || {}).map(([key, value]) => (
              <div className="flag-pill" key={key}>
                <span>{key.replaceAll("_", " ")}</span>
                <strong>{value ? "Yes" : "No"}</strong>
              </div>
            ))}
          </div>

          <h3>Saved Actions</h3>

          {audit.actions.length === 0 ? (
            <p className="muted-text">No saved agent actions for this email yet.</p>
          ) : (
            <div className="trace-list">
              {audit.actions.map((action) => (
                <ActionCard action={action} key={action.id} />
              ))}
            </div>
          )}
        </div>
      ) : null}

      {agentResult ? (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2>Latest Dry Run Result</h2>
              <p>{agentResult.email.subject}</p>
            </div>

            <Badge>{agentResult.final_decision.action_type}</Badge>
          </div>

          <div className="decision-grid">
            <div>
              <span>Auto Reply Allowed</span>
              <strong>
                {agentResult.final_decision.auto_reply_allowed ? "Yes" : "No"}
              </strong>
            </div>

            <div>
              <span>Requires Approval</span>
              <strong>
                {agentResult.final_decision.requires_approval ? "Yes" : "No"}
              </strong>
            </div>

            <div>
              <span>Execute Now</span>
              <strong>
                {agentResult.final_decision.execute_now ? "Yes" : "No"}
              </strong>
            </div>

            <div>
              <span>Reason</span>
              <strong>{agentResult.final_decision.reason}</strong>
            </div>
          </div>

          {agentResult.proposed_reply ? (
            <>
              <h3>Proposed Reply</h3>
              <div className="proposed-content">{agentResult.proposed_reply}</div>
            </>
          ) : (
            <p className="muted-text">
              No proposed reply was generated. This is expected for blocked cases such as security threats or spam.
            </p>
          )}

          <h3>Reasoning Trace</h3>
          <ReasoningTrace trace={agentResult.reasoning_trace} />
        </div>
      ) : null}
    </div>
  );
}