const badgeStyles = {
  Critical: "badge badge-critical",
  High: "badge badge-high",
  Medium: "badge badge-medium",
  Low: "badge badge-low",
  Escalated: "badge badge-critical",
  Processing: "badge badge-medium",
  Received: "badge badge-low",
  Ignored: "badge badge-muted",
  Legal: "badge badge-critical",
  Complaint: "badge badge-high",
  Spam: "badge badge-muted",
  Internal: "badge badge-muted",
};

export default function Badge({ children }) {
  const className = badgeStyles[children] || "badge";

  return <span className={className}>{children}</span>;
}