import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getCategoryBreakdown,
  getSentimentTrend,
} from "../api/client";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";

export default function AnalyticsPage() {
  const [sentiment, setSentiment] = useState(null);
  const [breakdown, setBreakdown] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const [sentimentResult, breakdownResult] = await Promise.all([
          getSentimentTrend({ days: 30 }),
          getCategoryBreakdown({ days: 30 }),
        ]);

        setSentiment(sentimentResult);
        setBreakdown(breakdownResult);
      } catch (err) {
        setError(
          err?.response?.data?.error?.message ||
            err.message ||
            "Could not load analytics."
        );
      }
    }

    loadAnalytics();
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!sentiment || !breakdown) {
    return <LoadingState message="Loading analytics..." />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Analytics</p>
          <h1>Sentiment and Workload Analytics</h1>
          <p>
            Dataset anchored at {sentiment.anchor_time}. Deterioration alert:{" "}
            <strong>{sentiment.deterioration_alert ? "Yes" : "No"}</strong>
          </p>
        </div>
      </div>

      <section className="content-grid">
        <div className="panel">
          <div className="panel-header">
            <h2>Sentiment Trend</h2>
          </div>

          <div className="chart-box">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={sentiment.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="average_sentiment_score"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="moving_average_3_day"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Category Breakdown</h2>
          </div>

          <div className="chart-box">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={breakdown.category_breakdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
    </div>
  );
}