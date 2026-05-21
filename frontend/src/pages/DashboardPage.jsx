import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Inbox,
  MessageSquareWarning,
  ShieldAlert,
  Users,
} from "lucide-react";

import { getDashboardStats } from "../api/client";
import Badge from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import StatCard from "../components/StatCard";

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const result = await getDashboardStats();
        setData(result);
      } catch (err) {
        setError(
          err?.response?.data?.error?.message ||
            err.message ||
            "Could not load dashboard stats."
        );
      }
    }

    loadDashboard();
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState message="Loading CRM intelligence dashboard..." />;
  }

  const summary = data.summary;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Mission Control</p>
          <h1>CRM Intelligence Dashboard</h1>
          <p>
            Live overview of ingested emails, escalations, spam filtering, and
            human-review workload.
          </p>
        </div>
      </div>

      <section className="stats-grid">
        <StatCard
          title="Total Emails"
          value={summary.total_emails}
          description="Messages ingested from stream"
          icon={Inbox}
        />
        <StatCard
          title="Total Contacts"
          value={summary.total_contacts}
          description="Unique senders detected"
          icon={Users}
        />
        <StatCard
          title="Escalated"
          value={summary.escalated}
          description="Requires human or specialist review"
          icon={AlertTriangle}
        />
        <StatCard
          title="Critical"
          value={summary.critical}
          description="Highest urgency cases"
          icon={ShieldAlert}
        />
        <StatCard
          title="Needs Human"
          value={summary.needs_human}
          description="Blocked from autonomous handling"
          icon={MessageSquareWarning}
        />
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="panel-header">
            <h2>Category Breakdown</h2>
          </div>

          <div className="list">
            {data.category_breakdown.map((item) => (
              <div className="list-row" key={item.category}>
                <div>
                  <Badge>{item.category}</Badge>
                </div>
                <strong>{item.count}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Latest Emails</h2>
          </div>

          <div className="email-list">
            {data.latest_emails.map((email) => (
              <article className="email-card" key={email.id}>
                <div className="email-card-top">
                  <strong>{email.subject}</strong>
                  <Badge>{email.urgency}</Badge>
                </div>

                <p>{email.sender}</p>

                <div className="email-meta">
                  <Badge>{email.category}</Badge>
                  <Badge>{email.status}</Badge>
                  <span>Priority {email.priority_score}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}